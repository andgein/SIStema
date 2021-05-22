import operator
import random

import collections
import django.urls
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Count, Sum, FloatField, IntegerField
from django.db.models.functions import Cast
from django.http.response import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import is_safe_url
from django.views.decorators.http import require_POST

import frontend.icons
import frontend.table
import groups.decorators
import modules.entrance.groups as entrance_groups
import modules.topics.views as topics_views
import questionnaire.models
import questionnaire.views
import sistema.staff
import users.models
import users.views
from frontend.table.utils import A, TableDataSource
from modules.ejudge import models as ejudge_models
from modules.entrance import models
from modules.entrance import upgrades
from modules.entrance import views as entrance_views
from modules.entrance.staff import forms
from sistema.helpers import group_by, respond_as_attachment, nested_query_list, list_to_dict
from users import search_utils
from .. import helpers


class EnrollingUsersTable(frontend.table.Table):
    name = frontend.table.LinkColumn(
        accessor='get_full_name',
        verbose_name='Имя',
        order_by=('profile.last_name',
                  'profile.first_name',
                  'profile.middle_name'),
        search_in=('profile.first_name',
                   'profile.middle_name',
                   'profile.last_name'),
        viewname='school:entrance:enrolling_user',
        args=[A('school_short_name'), A('id')])

    email = frontend.table.EmailColumn(
        accessor='email',
        orderable=True,
        searchable=True,
        verbose_name='Почта')

    city = frontend.table.Column(
        accessor='profile.city',
        orderable=True,
        searchable=True,
        verbose_name='Город')

    school_and_class = frontend.table.Column(
        accessor='profile',
        search_in='profile.school_name',
        verbose_name='Школа и класс')

    class Meta:
        icon = frontend.icons.FaIcon('envelope-o')
        title = 'Подавшие заявку'
        exportable = True

    def __init__(self, school, *args, **kwargs):
        qs = (users.models.User.objects
              .filter(entrance_statuses__school=school)
              .exclude(entrance_statuses__status=
                       models.EntranceStatus.Status.NOT_PARTICIPATED)
              .annotate(school_short_name=F('entrance_statuses__school'
                                            '__short_name'))
              .select_related('profile'))
        super().__init__(
            qs,
            django.urls.reverse('school:entrance:enrolling_data',
                                args=[school.short_name]),
            *args, **kwargs)

    def render_school_and_class(self, value):
        parts = []
        if value.school_name:
            parts.append(value.school_name)
        if value.current_class is not None:
            parts.append(str(value.current_class) + ' класс')
        return ', '.join(parts)

    def search_column_name(self, qs, query):
        pass


@sistema.staff.only_staff
def enrolling(request):
    users_table = EnrollingUsersTable(request.school)
    frontend.table.RequestConfig(request).configure(users_table)
    return render(
        request, 'entrance/staff/enrolling.html', {'users_table': users_table})


@sistema.staff.only_staff
def enrolling_data(request):
    users_table = EnrollingUsersTable(request.school)
    return TableDataSource(users_table).get_response(request)


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def user_profile(request, user_id):
    user = get_object_or_404(users.models.User, id=user_id)
    return users.views.profile_for_user(request, user)


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def user_questionnaire(request, user_id, questionnaire_name):
    user = get_object_or_404(users.models.User, id=user_id)
    # TODO: use staff interface for showing questionnaire (here, in user_profile() and in user_topics())
    return questionnaire.views.questionnaire_for_user(request, user, questionnaire_name)


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
@topics_views.topic_questionnaire_view
def user_topics(request, user_id):
    # TODO: check that status of topics questionnaire for this user is FINISHED
    user = get_object_or_404(users.models.User, id=user_id)
    return topics_views.show_final_answers(request, user)


def _remove_old_checking_locks():
    models.CheckingLock.objects.filter(locked_until__lt=timezone.now()).delete()


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def check(request):
    _remove_old_checking_locks()

    checking_groups = request.school.entrance_checking_groups.all()
    for checking_group in checking_groups:
        checking_group.group_users = list(checking_group.group.users)
        checking_group.group_tasks = list(checking_group.tasks.order_by('order'))

    return render(request, 'entrance/staff/check.html', {
        'checking_groups': checking_groups,
    })


class UserSummary:
    def __init__(self, class_number, school, city, previous_parallels, a_ml, entrance_reason_text, entrance_statuses):
        self.class_number = class_number
        self.school = school
        self.city = city
        self.previous_parallels = previous_parallels
        self.a_ml = a_ml
        self.entrance_reason_text = entrance_reason_text
        self.entrance_statuses = entrance_statuses

    @classmethod
    def get_answer(cls, user, school, answer_model, question_short_name):
        answer = answer_model.objects.filter(
            user=user,
            questionnaire__school=school,
            question_short_name=question_short_name
        ).first()
        return answer.answer if answer is not None else None

    @classmethod
    def summary_for_user(cls, school, user):
        AnswerModel = questionnaire.models.QuestionnaireAnswer
        VariantModel = questionnaire.models.ChoiceQuestionnaireQuestionVariant

        variant_by_id = {str(var.id): var for var in VariantModel.objects.all()}

        if hasattr(user, 'profile'):
            class_number = user.profile.current_class
            school_name = user.profile.school_name
            city = user.profile.city
        else:
            class_number = cls.get_answer(user, school, AnswerModel, 'class')
            school_name = cls.get_answer(user, school, AnswerModel, 'school')
            city = cls.get_answer(user, school, AnswerModel, 'city')

        entrance_reason_id = cls.get_answer(user, school, AnswerModel, 'entrance_reason')
        entrance_reason_text = variant_by_id[entrance_reason_id].text if entrance_reason_id else None

        prev_parallel_answers = AnswerModel.objects.filter(
            user=user,
            questionnaire__school=school,
            question_short_name='previous_parallels'
        )
        previous_parallels = [variant_by_id[ans.answer].text
                              for ans in prev_parallel_answers]

        a_ml = AnswerModel.objects.filter(
            user=user,
            questionnaire__school=school,
            question_short_name='a_ml'
        ).exists()

        entrance_statuses = list(models.EntranceStatus.objects.filter(user=user))

        return cls(class_number, school_name, city, previous_parallels, a_ml, entrance_reason_text, entrance_statuses)


def _find_clones(user):
    if not hasattr(user, 'profile'):
        return []
    similar_accounts = search_utils.SimilarAccountSearcher(user.profile).search(strict=False)
    return [similar_user for similar_user in similar_accounts if user.id != similar_user.id]


def check_user(request, user, group=None):
    entrance_exam: models.EntranceExam = (
        models.EntranceExam.objects.filter(school=request.school).first()
    )

    checking_comments = user.entrance_checking_comments.filter(
        school=request.school
    ).order_by('created_at')

    add_checking_comment_form = forms.AddCheckingCommentForm()

    base_entrance_level = None
    level_upgrades = []
    test_tasks = []
    file_tasks = []
    program_tasks = []
    if entrance_exam is not None:
        base_entrance_level = upgrades.get_base_entrance_level(request.school, user)
        _, tasks = entrance_views.get_entrance_level_and_tasks(request.school, user)
        level_upgrades = models.EntranceLevelUpgrade.objects.filter(
            upgraded_to__school=request.school,
            user=user
        )
        tasks_solutions = group_by(
            user.entrance_exam_solutions.filter(task__exam=entrance_exam).order_by('-created_at'),
            operator.attrgetter('task_id')
        )

        # Find solutions for tasks which are not in `tasks` (i.e. in case when
        # user selected entrance level, solved some tasks and changed
        # level later). Let's show these tasks on enrollment page too.
        # We mark these tasks by `from_another_level` attribute and append
        # them to the end of list.
        level_task_ids = {task.id for task in tasks}
        for task_id in set(tasks_solutions.keys()) - level_task_ids:
            task = models.EntranceExamTask.objects.get(id=task_id)
            task.from_another_level = True
            tasks.append(task)

        for task in tasks:
            task.user_solutions = tasks_solutions[task.id]
            task.is_solved = task.is_solved_by_user(user)
            if type(task) is models.TestEntranceExamTask:
                if len(task.user_solutions) > 0:
                    task.last_try = task.user_solutions[0].solution
                    task.is_last_correct = task.is_solution_correct(task.last_try)
                else:
                    task.last_try = None
                    task.is_last_correct = None
            if type(task) is models.FileEntranceExamTask:
                if len(task.user_solutions) > 0:
                    task.last_solution = task.user_solutions[0]
                    task.checks = list(task.last_solution.checks.all())
                else:
                    task.last_solution = None
                    task.checks = []


        test_tasks = list(filter(
            lambda t: type(t) is models.TestEntranceExamTask, tasks
        ))
        file_tasks = list(filter(
            lambda t: type(t) is models.FileEntranceExamTask, tasks
        ))
        program_tasks = list(filter(
            lambda t: isinstance(t, models.EjudgeEntranceExamTask), tasks
        ))

    return render(request, 'entrance/staff/check_user.html', {
        'group': group,
        'user_for_checking': user,
        'base_entrance_level': base_entrance_level,
        'level_upgrades': level_upgrades,

        'can_participant_select_entrance_level': entrance_exam.can_participant_select_entrance_level if entrance_exam else False,
        'selected_entrance_level': entrance_views.get_entrance_level_selected_by_user(request.school, user, base_entrance_level),

        'test_tasks': test_tasks,
        'file_tasks': file_tasks,
        'program_tasks': program_tasks,

        'checking_comments': checking_comments,
        'add_checking_comment_form': add_checking_comment_form,

        'user_summary': UserSummary.summary_for_user(request.school, user),
        'clone_accounts': _find_clones(user)
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def check_group(request, group_name):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name
    )
    _remove_old_checking_locks()

    tasks = list(checking_group.tasks.order_by('order'))
    group_user_ids = nested_query_list(checking_group.group.user_ids)
    for task in tasks:
        task.solutions_count = users.models.User.objects.filter(
            id__in=group_user_ids,
            entrance_exam_solutions__task=task
        ).distinct().count()
        task.checks = models.CheckedSolution.objects.filter(
            solution__task=task,
            solution__user_id__in=group_user_ids
        )
        task.checked_solutions_count = task.checks.values_list(
            'solution__user_id', flat=True
        ).distinct().count()
        task.checks_count = task.checks.count()

    group_checks = models.CheckedSolution.objects.filter(
        solution__task__in=tasks,
        solution__user_id__in=group_user_ids
    )
    total_solutions_count = sum(task.solutions_count for task in tasks)
    total_checked_solutions_count = sum(task.checked_solutions_count for task in tasks)
    total_checks_count = sum(task.checks_count for task in tasks)
    total_teachers_count = (
        group_checks.order_by('checked_by_id')
            .values('checked_by_id')
            .distinct()
            .count()
    )
    total_users_count = len(group_user_ids)

    for task in tasks:
        task.checks = list(task.checks.order_by('-created_at')[:20])

    return render(request, 'entrance/staff/check_group.html', {
        'group': checking_group,
        'tasks': tasks,

        'total_solutions_count': total_solutions_count,
        'total_checks_count': total_checks_count,
        'total_checked_solutions_count': total_checked_solutions_count,
        'total_teachers_count': total_teachers_count,
        'total_users_count': total_users_count,
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def checking_group_users(request, group_name):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    users = checking_group.group.users.select_related('profile')
    tasks = list(checking_group.tasks.order_by('order'))
    user_ids = [u.id for u in users]
    task_ids = [t.id for t in tasks]

    solutions = list(models.FileEntranceExamTaskSolution.objects.filter(
        user_id__in=user_ids,
        task_id__in=task_ids,
    ))
    checks = list(models.CheckedSolution.objects.filter(
        solution__user_id__in=user_ids,
        solution__task_id__in=task_ids,
    ).select_related('solution'))

    solutions_by_user = group_by(solutions, lambda s: s.user_id)
    solved_tasks_count_by_user = {
        user_id: len({s.task_id for s in solutions})
        for user_id, solutions in solutions_by_user.items()
    }
    checks_by_user = group_by(checks, lambda c: c.solution.user_id)
    checked_tasks_count_by_user = {
        user_id: len({c.solution.task_id for c in checks})
        for user_id, checks in checks_by_user.items()
    }

    return render(request, 'entrance/staff/group_users.html', {
        'group': checking_group,
        'users': users,
        'tasks': tasks,
        'solutions': solutions,
        'checks': checks,
        'solved_tasks_count_by_user':
            collections.defaultdict(int, solved_tasks_count_by_user),
        'checked_tasks_count_by_user':
            collections.defaultdict(int, checked_tasks_count_by_user),
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def checking_group_teachers(request, group_name):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    user_ids = list(checking_group.group.user_ids)
    tasks = list_to_dict(
        checking_group.tasks.order_by('order'),
        lambda task: task.id,
        lambda task: task
    )
    task_ids = list(tasks.keys())

    checks = models.CheckedSolution.objects.filter(
        solution__user_id__in=user_ids,
        solution__task_id__in=task_ids,
    ).select_related('solution', 'checked_by')
    checks_grouped_by_teacher = checks.values('checked_by_id')
    checks_grouped_by_task_and_teacher = (
        checks.values('solution__task_id', 'checked_by_id')
    )

    teacher_solutions_count = list_to_dict(
        checks_grouped_by_teacher.annotate(count=Count('solution_id', distinct=True)),
        operator.itemgetter('checked_by_id'),
        operator.itemgetter('count'),
    )
    teacher_task_solutions_count = list_to_dict(
        checks_grouped_by_task_and_teacher.annotate(count=Count('solution_id', distinct=True)),
        operator.itemgetter('checked_by_id'),
        operator.itemgetter('solution__task_id'),
        operator.itemgetter('count'),
    )
    average_scores = list_to_dict(
        checks_grouped_by_task_and_teacher.annotate(
            average_score=sql_round_with_precision(
                Cast(Sum('score'), FloatField()) / Cast(Count('score'), FloatField()),
                2
            )
        ),
        operator.itemgetter('checked_by_id'),
        operator.itemgetter('solution__task_id'),
        operator.itemgetter('average_score'),
    )
    teacher_tasks = group_by(
        checks_grouped_by_task_and_teacher.distinct(),
        operator.itemgetter('checked_by_id'),
        extract_value_function=operator.itemgetter('solution__task_id')
    )

    teacher_ids = nested_query_list(
        checks.order_by('checked_by_id')
              .values_list('checked_by_id', flat=True)
              .distinct()
    )
    teachers = users.models.User.objects.filter(id__in=teacher_ids)
    ordered_teachers = sorted(
        teachers,
        key=lambda t: teacher_solutions_count[t.id],
        reverse=True
    )
    return render(request, 'entrance/staff/group_teachers.html', {
        'group': checking_group,
        'tasks': tasks,
        'teachers': ordered_teachers,
        'teacher_solutions_count': teacher_solutions_count,
        'teacher_tasks': teacher_tasks,
        'teacher_task_solutions_count': teacher_task_solutions_count,
        'average_scores': average_scores,
    })


def sql_round_with_precision(expression, precision):
    multiplier = 10 ** precision
    # Multiply and truncate non-integer part
    multiplied = Cast(multiplier * expression, IntegerField())
    return Cast(multiplied, FloatField()) / multiplier


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def checking_group_checks(request, group_name):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    tasks = list(checking_group.tasks.order_by('order'))
    user_ids = nested_query_list(checking_group.group.user_ids)
    task_ids = [t.id for t in tasks]

    checks = list(
        models.CheckedSolution.objects.filter(
            solution__user_id__in=user_ids,
            solution__task_id__in=task_ids,
        ).order_by('-created_at')
            .select_related('solution__user')
            .select_related('solution__task')
    )

    return render(request, 'entrance/staff/group_checks.html', {
        'group': checking_group,
        'users': users,
        'tasks': tasks,
        'checks': checks,
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def task_checks(request, group_name, task_id):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )
    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)
    if not checking_group.tasks.filter(id=task.id).exists():
        return HttpResponseNotFound()

    group_user_ids = nested_query_list(checking_group.group.user_ids)

    checks = (
        models.CheckedSolution.objects.filter(
            solution__user_id__in=group_user_ids,
            solution__task_id=task_id,
        ).order_by('-created_at')
            .select_related('solution__user')
            .select_related('solution__task')
    )

    return render(request, 'entrance/staff/group_checks.html', {
        'group': checking_group,
        'users': users,
        'task': task,
        'checks': checks,
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def teacher_checks(request, group_name, teacher_id):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )
    teacher = get_object_or_404(users.models.User, pk=teacher_id)

    group_user_ids = nested_query_list(checking_group.group.user_ids)

    checks = (
        models.CheckedSolution.objects.filter(
            solution__user_id__in=group_user_ids,
            checked_by=teacher
        ).order_by('-created_at')
            .select_related('solution__user')
            .select_related('solution__task')
    )

    return render(request, 'entrance/staff/teacher_checks.html', {
        'group': checking_group,
        'teacher': teacher,
        'checks': checks,
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def teacher_task_checks(request, group_name, teacher_id, task_id):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )
    teacher = get_object_or_404(users.models.User, pk=teacher_id)

    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)
    if not checking_group.tasks.filter(id=task.id).exists():
        return HttpResponseNotFound()

    group_user_ids = nested_query_list(checking_group.group.user_ids)

    checks = (
        models.CheckedSolution.objects.filter(
            solution__user_id__in=group_user_ids,
            solution__task_id=task_id,
            checked_by=teacher
        ).order_by('-created_at')
            .select_related('solution__user')
            .select_related('solution__task')
    )

    return render(request, 'entrance/staff/teacher_checks.html', {
        'group': checking_group,
        'teacher': teacher,
        'task': task,
        'checks': checks,
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def check_task(request, group_name, task_id):
    checking_group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    _remove_old_checking_locks()

    if not checking_group.tasks.filter(id=task_id).exists():
        return redirect('school:entrance:check',
                        school_name=request.school.short_name,
                        )

    lock = request.user.entrance_checking_locks_by_user.first()
    if lock is not None:
        messages.add_message(
            request, messages.INFO,
            'Вам необходимо допроверить выбранную работу или отказаться от проверки'
        )
        return redirect(
            'school:entrance:check_users_task',
            school_name=request.school.short_name,
            group_name=group_name,
            user_id=lock.user_id,
            task_id=lock.task_id
        )

    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)

    with transaction.atomic():
        locked_user_ids = set(
            models.CheckingLock.objects
                .filter(task=task)
                .values_list('user_id', flat=True)
        )
        task_user_ids = set(task.solutions.values_list('user_id', flat=True))
        already_checked_user_ids = set(models.CheckedSolution.objects.filter(
            solution__task=task
        ).values_list('solution__user_id', flat=True))

        users_for_checking = (
            checking_group.group.users
                .exclude(id__in=locked_user_ids)
                .exclude(id__in=already_checked_user_ids)
                .filter(id__in=task_user_ids)
        )

        users_count = users_for_checking.count()

        if users_count == 0:
            messages.add_message(
                request, messages.INFO,
                'Все решения задачи «%s» проверены' % (task.title,)
            )
            return redirect('school:entrance:check_group',
                            school_name=request.school.short_name,
                            group_name=group_name,
                            )

        # Get the random user for checking
        user_index = random.randint(0, users_count - 1)
        user_for_checking = users_for_checking[user_index]
        models.CheckingLock.objects.create(
            user=user_for_checking,
            task=task,
            locked_by=request.user
        )

    return redirect('school:entrance:check_users_task',
                    school_name=request.school.short_name,
                    group_name=group_name,
                    task_id=task.id,
                    user_id=user_for_checking.id,
                    )


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def check_users_task(request, task_id, user_id, group_name=None):
    _remove_old_checking_locks()

    if group_name is not None:
        checking_group = get_object_or_404(
            models.CheckingGroup,
            school=request.school,
            short_name=group_name
        )
    else:
        checking_group = None

    user = get_object_or_404(users.models.User, id=user_id)
    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)
    task.mark_field_id = (
        forms.FileEntranceExamTasksMarkForm.FIELD_ID_TEMPLATE % task.id
    )
    task.comment_field_id = (
        forms.FileEntranceExamTasksMarkForm.COMMENT_ID_TEMPLATE % task.id
    )

    if checking_group is None:
        group_user_ids = list({
            user_id
            for g in request.school.entrance_checking_groups.all()
            for user_id in g.group.user_ids
        })
    else:
        # Select users from group
        group_user_ids = checking_group.group.user_ids

    task.total_solutions_count = users.models.User.objects.filter(
        id__in=nested_query_list(group_user_ids),
        entrance_exam_solutions__task=task
    ).distinct().count()
    task.checked_solutions_count = users.models.User.objects.filter(
        id__in=nested_query_list(group_user_ids),
        entrance_exam_solutions__task=task,
        entrance_exam_solutions__checks__isnull=False
    ).distinct().count()

    locked_by_me = True
    with transaction.atomic():
        lock = models.CheckingLock.objects.filter(
            user=user,
            task=task,
        ).first()
        if lock is None:
            lock = models.CheckingLock.objects.create(
                user_id=user_id,
                task_id=task_id,
                locked_by=request.user,
            )
        else:
            locked_by_me = lock.locked_by_id == request.user.id

    base_entrance_level = upgrades.get_base_entrance_level(
        request.school, user
    )
    level_upgrades = models.EntranceLevelUpgrade.objects.filter(
        upgraded_to__school=request.school,
        user=user
    )

    solutions = task.solutions.filter(user=user).order_by('-created_at')
    if not solutions.exists():
        lock.delete()
        messages.add_message(
            request, messages.INFO,
            'Этот пользователь не решал выбранную задачу'
        )
        if checking_group is None:
            return redirect('school:entrance:enrolling_user',
                            school_name=request.school.short_name,
                            user_id=user.id)
        return redirect('school:entrance:check_task',
                        school_name=request.school.short_name,
                        group_name=group_name,
                        task_id=task.id)

    solutions = list(solutions)
    last_solution = solutions[0]

    if request.method == 'POST':
        if 'refuse' in request.POST:
            lock.delete()
            return redirect(
                'school:entrance:check',
                school_name=request.school.short_name,
            )

        mark_form = forms.FileEntranceExamTasksMarkForm(
            [task], request.POST, with_comment=True
        )
        if mark_form.is_valid():
            score = mark_form.cleaned_data[task.mark_field_id]
            comment = mark_form.cleaned_data[task.comment_field_id]
            models.CheckedSolution.objects.create(
                solution=last_solution,
                checked_by=request.user,
                score=score,
                comment=comment
            )
            lock.delete()

            messages.add_message(
                request, messages.INFO,
                'Баллы пользователю %s успешно сохранены' % (user.get_full_name(),)
            )

            if checking_group is None:
                return redirect('school:entrance:enrolling_user',
                                school_name=request.school.short_name,
                                user_id=user.id)

            return redirect(
                'school:entrance:check_task',
                school_name=request.school.short_name,
                group_name=group_name,
                task_id=task.id
            )
    else:
        mark_form = forms.FileEntranceExamTasksMarkForm(
            [task], with_comment=True
        )

    checks = list(models.CheckedSolution.objects.filter(
        solution=last_solution
    ).order_by('-created_at'))
    last_mark = None if len(checks) == 0 else checks[0].score
    if last_mark is not None:
        mark_form.set_initial_mark(task.id, last_mark)

    checking_comments = models.CheckingComment.objects.filter(
        school=request.school,
        user=user
    )

    add_checking_comment_form = forms.AddCheckingCommentForm()

    return render(request, 'entrance/staff/check_users_task.html', {
        'group': checking_group,
        'user_for_checking': user,
        'locked_by_me': locked_by_me,
        'task': task,

        'base_entrance_level': base_entrance_level,
        'level_upgrades': level_upgrades,

        'can_participant_select_entrance_level': task.exam.can_participant_select_entrance_level,
        'selected_entrance_level': entrance_views.get_entrance_level_selected_by_user(
            request.school, user, base_entrance_level),

        'solutions': solutions,
        'last_solution': last_solution,
        'checks': checks,
        'last_mark': last_mark,
        'checking_comments': checking_comments,
        'add_checking_comment_form': add_checking_comment_form,

        'mark_form': mark_form
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.ADMINS)
def enrolling_user(request, user_id):
    user = get_object_or_404(users.models.User, id=user_id)
    _remove_old_checking_locks()

    return check_user(request, user)


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.CAN_CHECK)
def solution(request, solution_id):
    solution = get_object_or_404(models.EntranceExamTaskSolution, id=solution_id)

    if type(solution) is models.FileEntranceExamTaskSolution:
        original_filename = solution.original_filename
        return respond_as_attachment(
            request,
            solution.solution,
            '%06d_%s' % (int(solution.id), original_filename)
        )

    if isinstance(solution, models.EjudgeEntranceExamTaskSolution):
        return respond_as_attachment(
            request,
            solution.solution,
            '%06d' % int(solution.id)
        )

    return HttpResponseNotFound()


@sistema.staff.only_staff
@require_POST
def add_comment(request, user_id):
    redirect_url = request.POST.get('next', '')
    if not is_safe_url(redirect_url, request.get_host()):
        redirect_url = reverse('school:entrance:enrolling_user', kwargs={
            'school_name': request.school.short_name,
            'user_id': user_id,
        })

    form = forms.AddCheckingCommentForm(data=request.POST)
    if form.is_valid():
        models.CheckingComment.objects.create(
            school=request.school,
            user_id=user_id,
            comment=form.cleaned_data['comment'],
            commented_by=request.user,
        )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            form['comment'].errors[0]
        )

    return redirect(redirect_url)


def _get_ejudge_task_accepted_solutions(school, solution_model):
    return solution_model.objects.filter(
        task__exam__school=school,
        ejudge_queue_element__submission__result__result=ejudge_models.CheckingResult.Result.OK
    )


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.ADMINS)
def initial_auto_reject(request):
    user_ids = list(helpers.get_enrolling_users_ids(request.school))

    practice_user_ids = set(_get_ejudge_task_accepted_solutions(
        request.school, models.ProgramEntranceExamTaskSolution
    ).values_list('user_id', flat=True))
    practice_user_ids.update(set(_get_ejudge_task_accepted_solutions(
        request.school, models.OutputOnlyEntranceExamTaskSolution
    ).values_list('user_id', flat=True)))

    theory_user_ids = set(models.FileEntranceExamTaskSolution.objects.filter(
        task__exam__school=request.school,
    ).values_list('user_id', flat=True))

    already_in_groups_user_ids = {
        user_id
        for g in request.school.entrance_checking_groups.all()
        for user_id in g.group.user_ids
    }

    user_ids = set(user_ids) - already_in_groups_user_ids

    for user_id in user_ids:
        reason = None
        if user_id not in practice_user_ids:
            reason = 'Не решено полностью ни одной практической задачи'
        if user_id not in theory_user_ids:
            reason = 'Не сдано ни одной теоретический задачи'
        if reason is not None:
            models.EntranceStatus.objects.update_or_create(
                school=request.school,
                user_id=user_id,
                defaults={
                    'public_comment': reason,
                    'is_status_visible': False,
                    'status': models.EntranceStatus.Status.AUTO_REJECTED
                })

    return JsonResponse({
        'rejected': [{
            'user_id': s.user_id,
            'public_comment': s.public_comment,
            'is_status_visible': s.is_status_visible,
        } for s in models.EntranceStatus.objects.filter(
            school=request.school,
            status=models.EntranceStatus.Status.AUTO_REJECTED
        )]
    })


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.ENROLLMENT_TYPE_REVIEWERS)
def review_enrollment_type_for_user(request, user_id):
    user = get_object_or_404(users.models.User, id=user_id)
    entrance_step = get_object_or_404(
        models.SelectEnrollmentTypeEntranceStep,
        school=request.school,
    )
    selected_enrollment_type = get_object_or_404(
        models.SelectedEnrollmentType,
        user=user,
        step=entrance_step,
        enrollment_type__needs_moderation=True,
    )

    # TODO(artemtab): add locking
    # locked_by_me = True
    # with transaction.atomic():

    base_entrance_level = upgrades.get_base_entrance_level(
        request.school, user)
    level_upgrades = models.EntranceLevelUpgrade.objects.filter(
        upgraded_to__school=request.school,
        user=user
    )
    topics_entrance_level = upgrades.get_topics_entrance_level(
        request.school, user)

    if request.method == 'POST':
        pass
        # Handle review
    else:
        pass
        # Initialize review form

    add_checking_comment_form = forms.AddCheckingCommentForm()
    checking_comments = models.CheckingComment.objects.filter(
        school=request.school,
        user=user
    )

    # TODO(artemtab): better ordering, now it's not exactly chronological
    participations = (
        user.school_participations
            .order_by('-school__year', '-school__name'))

    return render(request, 'entrance/staff/enrollment_review_user.html', {
        'user_for_review': user,
        'participations': participations,

        'base_entrance_level': base_entrance_level,
        'level_upgrades': level_upgrades,
        'topics_entrance_level': topics_entrance_level,

        'can_participant_select_entrance_level': request.school.entrance_exam.can_participant_select_entrance_level,
        'selected_entrance_level': entrance_views.get_entrance_level_selected_by_user(
            request.school, user, base_entrance_level),

        'selected_enrollment_type': selected_enrollment_type,
        'review_info': entrance_step.review_info,
        # 'locked_by_me': locked_by_me,

        'add_checking_comment_form': add_checking_comment_form,
        'checking_comments': checking_comments,
    })
