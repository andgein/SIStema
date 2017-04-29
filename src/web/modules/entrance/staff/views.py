import operator
import random
import collections

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http.response import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

import frontend.icons
import frontend.table
import modules.topics.views as topics_views
import questionnaire.models
import questionnaire.views
import schools.models
import sistema.staff
import users.models
import users.views
from modules.ejudge.models import CheckingResult
from sistema.helpers import group_by, respond_as_attachment
from . import forms
from .. import models
from .. import upgrades


class EnrollingUsersTable(frontend.table.Table):
    icon = frontend.icons.FaIcon('envelope-o')

    title = 'Подавшие заявку'

    def __init__(self, school, users_ids):
        super().__init__(users.models.User, users.models.User.objects.filter(id__in=users_ids))
        self.school = school
        self.identifiers = {'school_name': school.short_name}

        self.about_questionnaire = questionnaire.models.Questionnaire.objects.filter(short_name='about').first()
        self.enrollee_questionnaire = questionnaire.models.Questionnaire.objects.filter(
                school=self.school,
                short_name='enrollee'
        ).first()

        name_column = frontend.table.SimplePropertyColumn(
                'get_full_name', 'Имя',
                search_attrs=['profile__first_name', 'profile__last_name'])
        name_column.data_type = frontend.table.LinkDataType(
                frontend.table.StringDataType(),
                lambda user: reverse('school:entrance:enrolling_user', args=(self.school.short_name, user.id))
        )

        email_column = frontend.table.SimplePropertyColumn('email', 'Почта')
        email_column.data_type = frontend.table.LinkDataType(
                frontend.table.StringDataType(),
                lambda user: 'mailto:%s' % user.email
        )

        self.columns = (name_column,
                        email_column,
                        frontend.table.SimpleFuncColumn(self.city, 'Город'),
                        frontend.table.SimpleFuncColumn(self.school_and_class, 'Школа и класс')
                        )

    # TODO: bad architecture :(
    # We need to define create for calling .after_filter_applying() without any filter.
    # Need refactoring
    @classmethod
    def create(cls, school):
        users_ids = get_enrolling_users_ids(school)
        table = cls(school, users_ids)
        table.after_filter_applying()
        return table

    def after_filter_applying(self):
        # TODO: use only id's via .values_list('id', flat=True)?
        filtered_users = list(self.paged_queryset)

        self.about_questionnaire_answers = group_by(
                questionnaire.models.QuestionnaireAnswer.objects.filter(
                        questionnaire=self.about_questionnaire,
                        user__in=filtered_users
                ),
                operator.attrgetter('user_id')
        )

        self.enrollee_questionnaire_answers = group_by(
                questionnaire.models.QuestionnaireAnswer.objects.filter(
                        questionnaire=self.enrollee_questionnaire,
                        user__in=filtered_users
                ),
                operator.attrgetter('user_id')
        )

    def get_header(self):
        pass

    @classmethod
    def restore(cls, identifiers):
        school_name = identifiers['school_name'][0]
        school_qs = schools.models.School.objects.filter(short_name=school_name)
        if not school_qs.exists():
            raise NameError('Bad school name')
        _school = school_qs.first()
        users_ids = get_enrolling_users_ids(_school)
        return cls(_school, users_ids)

    @staticmethod
    def _get_questionnaire_answer(questionnaire_answers, field):
        for answer in questionnaire_answers:
            if answer.question_short_name == field:
                return answer.answer
        return ''

    def _get_user_about_field(self, user, field):
        return self._get_questionnaire_answer(self.about_questionnaire_answers[user.id], field)

    def _get_user_enrollee_field(self, user, field):
        return self._get_questionnaire_answer(self.enrollee_questionnaire_answers[user.id], field)

    def city(self, user):
        return self._get_user_about_field(user, 'city')

    def school_and_class(self, user):
        user_school = self._get_user_about_field(user, 'school')
        user_class = self._get_user_enrollee_field(user, 'class')
        if user_school == '':
            return '%s класс' % user_class
        return '%s, %s класс' % (user_school, user_class)


def get_enrolling_users_ids(school):
    return models.EntranceStatus.objects.filter(
        school=school
    ).exclude(
        status=models.EntranceStatus.Status.NOT_PARTICIPATED
    ).values_list('user_id', flat=True)


@sistema.staff.only_staff
def enrolling(request):
    users_table = EnrollingUsersTable.create(request.school)
    return render(request, 'entrance/staff/enrolling.html', {'users_table': users_table})


@sistema.staff.only_staff
def user_profile(request, user_id):
    user = get_object_or_404(users.models.User, id=user_id)
    return users.views.profile_for_user(request, user)


@sistema.staff.only_staff
def user_questionnaire(request, user_id, questionnaire_name):
    user = get_object_or_404(users.models.User, id=user_id)
    # TODO: use staff interface for showing questionnaire (here, in user_profile() and in user_topics())
    return questionnaire.views.questionnaire_for_user(request, user, questionnaire_name)


@sistema.staff.only_staff
@topics_views.topic_questionnaire_view
def user_topics(request, user_id):
    # TODO: check that status of topics questionnaire for this user is FINISHED
    user = get_object_or_404(users.models.User, id=user_id)
    return topics_views.show_final_answers(request, user)


@sistema.staff.only_staff
@require_POST
def change_group(request, user_id):
    user = get_object_or_404(users.models.User, id=user_id)
    form = forms.MoveIntoCheckingGroupForm(request.school, data=request.POST)

    if form.is_valid():
        group = get_object_or_404(models.CheckingGroup, school=request.school, id=form.cleaned_data.get('group_id'))
        models.UserInCheckingGroup.move_user_into_group(user, group)

    return redirect('school:entrance:enrolling_user', school_name=request.school.short_name, user_id=user.id)


def _remove_old_checking_locks():
    models.CheckingLock.objects.filter(locked_until__lt=timezone.now()).delete()


@sistema.staff.only_staff
def check(request):
    _remove_old_checking_locks()

    checking_groups = request.school.entrance_checking_groups.all()
    for group in checking_groups:
        group.group_users = list(group.actual_users)
        group.group_tasks = list(group.tasks.order_by('order'))

    return render(request, 'entrance/staff/check.html', {
        'checking_groups': checking_groups,
    })


@sistema.staff.only_staff
def results(request):
    return None


class UserSummary:
    def __init__(self, class_number, school, city, previous_parallels, a_ml):
        self.class_number = class_number
        self.school = school
        self.city = city
        self.previous_parallels = previous_parallels
        self.a_ml = a_ml

    @classmethod
    def get_answer(cls, user, answer_model, question_short_name):
        answer = answer_model.objects.filter(
                user=user,
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
            class_number = 'N/A'
            school_name = 'N/A'
            city = 'N/A'

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

        return cls(class_number, school_name, city, previous_parallels, a_ml)


def check_user(request, user, checking_group=None):
    entrance_exam = models.EntranceExam.objects.filter(school=request.school).first()
    base_entrance_level = upgrades.get_base_entrance_level(request.school, user)
    level_upgrades = models.EntranceLevelUpgrade.objects.filter(
        upgraded_to__school=request.school,
        user=user
    )
    tasks = upgrades.get_entrance_tasks(
        request.school,
        user,
        base_entrance_level
    )
    tasks_solutions = group_by(
        user.entrance_exam_solutions.filter(task__exam=entrance_exam).order_by('-created_at'),
        operator.attrgetter('task_id')
    )

    for task in tasks:
        task.user_solutions = tasks_solutions[task.id]
        task.is_solved = task.is_solved_by_user(user)
        if type(task) is models.TestEntranceExamTask:
            if len(task.user_solutions) > 0:
                task.last_try = task.user_solutions[0].solution
                task.is_last_correct = task.check_solution(task.last_try)
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

    move_into_checking_group_form = forms.MoveIntoCheckingGroupForm(request.school)

    checking_comments = user.entrance_checking_comments.filter(school=request.school).order_by('created_at')

    return render(request, 'entrance/staff/check_user.html', {
        'checking_group': checking_group,
        'user_for_checking': user,
        'base_entrance_level': base_entrance_level,
        'level_upgrades': level_upgrades,

        'test_tasks': test_tasks,
        'file_tasks': file_tasks,
        'program_tasks': program_tasks,

        'checking_comments': checking_comments,
        'move_into_checking_group_form': move_into_checking_group_form,

        'user_summary': UserSummary.summary_for_user(
            request.school,
            user
        ),
    })


@sistema.staff.only_staff
def check_group(request, group_name):
    group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name
    )
    _remove_old_checking_locks()

    lock = request.user.entrance_checking_locks_by_user.first()
    if lock is not None:
        messages.add_message(
            request, messages.INFO,
            'Вам необходимо допроверить выбранную работу или отказаться от проверки'
        )
        return redirect(
            'school:entrance:check_users_task',
            school_name=request.school.short_name,
            group_name=group_name,
            user_id=lock.user_id,
            task_id=lock.task_id
        )

    tasks = list(group.tasks.order_by('order'))
    group_users_ids = list(group.actual_users.values_list('user_id', flat=True))
    for task in tasks:
        task.solutions_count = len(set(
            task.solutions
                .filter(user_id__in=group_users_ids)
                .values_list('user_id', flat=True)
        ))
        task.checks = models.CheckedSolution.objects.filter(
            solution__task=task,
            solution__user_id__in=group_users_ids
        )
        task.checked_solutions_count = len(set(
            task.checks.values_list('solution__user_id', flat=True)
        ))
        task.checks = list(task.checks.order_by('-created_at')[:20])

    return render(request, 'entrance/staff/check_group.html', {
        'group': group,
        'tasks': tasks,
    })


@sistema.staff.only_staff
def checking_group_users(request, group_name):
    group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    users = [u.user for u in group.actual_users.prefetch_related('user__profile')]
    tasks = list(group.tasks.order_by('order'))
    users_ids = [u.id for u in users]
    tasks_ids = [t.id for t in tasks]

    solutions = list(models.FileEntranceExamTaskSolution.objects.filter(
        user_id__in=users_ids,
        task_id__in=tasks_ids,
    ))
    checks = list(models.CheckedSolution.objects.filter(
        solution__user_id__in=users_ids,
        solution__task_id__in=tasks_ids,
    ).prefetch_related('solution'))

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
        'group': group,
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
def checking_group_checks(request, group_name):
    group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    users = [u.user for u in
             group.actual_users.prefetch_related('user__profile')]
    tasks = list(group.tasks.order_by('order'))
    users_ids = [u.id for u in users]
    tasks_ids = [t.id for t in tasks]

    checks = list(
        models.CheckedSolution.objects.filter(
            solution__user_id__in=users_ids,
            solution__task_id__in=tasks_ids,
        ).order_by('-created_at')
         .prefetch_related('solution__user')
         .prefetch_related('solution__task')
    )

    return render(request, 'entrance/staff/group_checks.html', {
        'group': group,
        'users': users,
        'tasks': tasks,
        'checks': checks,
    })


@sistema.staff.only_staff
def task_checks(request, group_name, task_id):
    group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )
    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)
    if task not in group.tasks.all():
        return HttpResponseNotFound()

    users = [u.user for u in
             group.actual_users.prefetch_related('user__profile')]
    users_ids = [u.id for u in users]

    checks = list(
        models.CheckedSolution.objects.filter(
            solution__user_id__in=users_ids,
            solution__task_id=task_id,
        ).order_by('-created_at')
         .prefetch_related('solution__user')
         .prefetch_related('solution__task')
    )

    return render(request, 'entrance/staff/group_checks.html', {
        'group': group,
        'users': users,
        'task': task,
        'checks': checks,
    })


@sistema.staff.only_staff
def check_task(request, group_name, task_id):
    group = get_object_or_404(
        models.CheckingGroup,
        school=request.school,
        short_name=group_name,
    )

    if not group.tasks.filter(id=task_id).exists():
        return redirect('school:entrance:check',
                        school_name=request.school.short_name,
                        )

    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)
    _remove_old_checking_locks()

    with transaction.atomic():
        locked_users_ids = set(models.CheckingLock.objects
                               .filter(task=task)
                               .values_list('user_id', flat=True))
        task_users_ids = set(task.solutions.values_list('user_id', flat=True))
        already_checked_users_ids = set(models.CheckedSolution.objects.filter(
            solution__task=task
        ).values_list('solution__user_id', flat=True))

        users_for_checking = (
            group.actual_users
            .exclude(user_id__in=locked_users_ids)
            .exclude(user_id__in=already_checked_users_ids)
            .filter(user_id__in=task_users_ids)
        )

        count = users_for_checking.count()

        if count == 0:
            messages.add_message(
                request, messages.INFO,
                'Все решения задачи «%s» проверены' % (task.title, )
            )
            return redirect('school:entrance:check_group',
                            school_name=request.school.short_name,
                            group_name=group_name,
                            )

        # Getting the random user for checking
        user_for_checking = users_for_checking[random.randint(0, count - 1)].user
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
def check_users_task(request, task_id, user_id, group_name=None):
    _remove_old_checking_locks()

    if group_name is not None:
        group = get_object_or_404(
            models.CheckingGroup,
            school=request.school,
            short_name=group_name
        )
    else:
        group = None

    user = get_object_or_404(users.models.User, id=user_id)
    task = get_object_or_404(models.FileEntranceExamTask, id=task_id)
    task.mark_field_id = (
        forms.FileEntranceExamTasksMarkForm.FIELD_ID_TEMPLATE % task.id
    )
    task.comment_field_id = (
        forms.FileEntranceExamTasksMarkForm.COMMENT_ID_TEMPLATE % task.id
    )

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
        if group is None:
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
                'Баллы пользователю %s успешно сохранены' % (user.get_full_name(), )
            )

            if group is None:
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

    move_into_checking_group_form = forms.MoveIntoCheckingGroupForm(request.school)

    return render(request, 'entrance/staff/check_users_task.html', {
        'group': group,
        'user_for_checking': user,
        'locked_by_me': locked_by_me,
        'task': task,

        'base_entrance_level': base_entrance_level,
        'level_upgrades': level_upgrades,

        'solutions': solutions,
        'last_solution': last_solution,
        'checks': checks,
        'last_mark': last_mark,
        'checking_comments': checking_comments,

        'move_into_checking_group_form': move_into_checking_group_form,
        'mark_form': mark_form
    })


@sistema.staff.only_staff
def enrolling_user(request, user_id):
    user = get_object_or_404(users.models.User, id=user_id)
    _remove_old_checking_locks()

    return check_user(request, user)


@sistema.staff.only_staff
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


def _get_ejudge_task_accepted_solutions(school, solution_model):
    return solution_model.objects.filter(
        task__exam__school=school,
        ejudge_queue_element__submission__result__result=CheckingResult.Result.OK
    )


@sistema.staff.only_staff
def initial_auto_reject(request):
    users_ids = list(get_enrolling_users_ids(request.school))

    practice_users_ids = set(_get_ejudge_task_accepted_solutions(
        request.school, models.ProgramEntranceExamTaskSolution
    ).values_list('user_id', flat=True))
    practice_users_ids.update(set(_get_ejudge_task_accepted_solutions(
        request.school, models.OutputOnlyEntranceExamTaskSolution
    ).values_list('user_id', flat=True)))

    theory_users_ids = set(models.FileEntranceExamTaskSolution.objects.filter(
        task__exam__school=request.school,
    ).values_list('user_id', flat=True))

    already_in_groups_users_ids = set(models.UserInCheckingGroup.objects.filter(
        group__school=request.school,
        is_actual=True
    ).values_list('user_id', flat=True))

    users_ids = set(users_ids) - already_in_groups_users_ids

    for user_id in users_ids:
        reason = None
        if user_id not in practice_users_ids:
            reason = 'Не решено полностью ни одной практической задачи'
        if user_id not in theory_users_ids:
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
def initial_checking_groups(request):
    return None
