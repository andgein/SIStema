from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http.response import HttpResponseNotFound, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

import ipware.ip
import operator

import questionnaire.models
import sistema.uploads
import sistema.helpers
import modules.topics.entrance.levels
import modules.ejudge.queue
from modules.entrance import forms
import modules.entrance.levels
import modules.entrance.staff.views as staff_views
from . import models
from . import upgrades
import frontend.table
import frontend.icons


def get_entrance_level_and_tasks(school, user):
    base_level = upgrades.get_base_entrance_level(school, user)
    tasks = upgrades.get_entrance_tasks(school, user, base_level)
    return base_level, tasks


# TODO: Inherit of staff_views.EnrollingUsersTable seems to be a bad architecture idea
class EntrancedUsersTable(staff_views.EnrollingUsersTable):
    icon = frontend.icons.FaIcon('check')

    search_enabled = False

    # Unlimited page
    page_size = None

    def __init__(self, school, users_ids):
        super().__init__(school, users_ids)
        self.title = 'Поступившие в ' + school.name

        entrance_statuses = (
            models.EntranceStatus.objects
                  .filter(
                      school=school,
                      user_id__in=users_ids,
                      is_status_visible=True)
                  .select_related('session', 'parallel')
                  .order_by('user__profile__last_name',
                      'user__profile__first_name'))
        self.status_by_user = sistema.helpers.group_by(entrance_statuses,
                                                       operator.attrgetter('user_id'))

        absence_reasons = (
            models.AbstractAbsenceReason.objects
                  .filter(school=school, user_id__in=users_ids))
        self.absence_reason_by_user_id = sistema.helpers.group_by(
            absence_reasons,
            operator.attrgetter('user_id')
        )

        enrolled_questionnaire = (questionnaire.models.Questionnaire.objects
                                               .filter(short_name='enrolled')
                                               .first())
        self.enrolled_questionnaire_answers_by_user_id = sistema.helpers.group_by(
            questionnaire.models.QuestionnaireAnswer.objects
                         .filter(questionnaire=enrolled_questionnaire,
                                 user__in=users_ids),
            operator.attrgetter('user_id')
        )

        index_column = frontend.table.IndexColumn()
        name_column = frontend.table.SimplePropertyColumn('get_full_name', 'Имя Фамилия')
        session_column = frontend.table.SimpleFuncColumn(self.get_session, 'Смена')
        parallel_column = frontend.table.SimpleFuncColumn(self.get_parallel, 'Параллель')
        enrolled_status_column = frontend.table.SimpleFuncColumn(self.get_enrolled_status,
                                                                 'Статус')
        self.columns = ((index_column, name_column) +
                        self.columns[2:] +
                        (session_column, parallel_column, enrolled_status_column))

    @classmethod
    def create(cls, school):
        entranced_users = models.EntranceStatus.objects.filter(
            school=school,
            status=models.EntranceStatus.Status.ENROLLED,
            is_status_visible=True,
        ).order_by('parallel', 'session')
        entranced_users_ids = entranced_users.values_list('user_id', flat=True)

        table = cls(school, entranced_users_ids)
        table.after_filter_applying()
        return table

    def get_session(self, user):
        if user.id not in self.status_by_user:
            return ''
        return self.status_by_user[user.id][0].session.name

    def get_parallel(self, user):
        if user.id not in self.status_by_user:
            return ''
        return self.status_by_user[user.id][0].parallel.name

    def get_enrolled_status(self, user):
        if user.id not in self.absence_reason_by_user_id:
            if user.id in self.enrolled_questionnaire_answers_by_user_id:
                return ''
            else:
                return 'Участие не подтверждено'
        return str(self.absence_reason_by_user_id[user.id][0])


@login_required
def exam(request, selected_task_id=None):
    entrance_exam = get_object_or_404(
        models.EntranceExam,
        school=request.school
    )
    is_closed = entrance_exam.is_closed()

    base_level, tasks = get_entrance_level_and_tasks(request.school, request.user)

    # Order task by type and order
    tasks = sorted(tasks, key=lambda t: (t.type_title, t.order))
    for task in tasks:
        task.user_solutions = list(
            task.solutions.filter(user=request.user).order_by('-created_at')
        )
        task.is_solved = task.is_solved_by_user(request.user)
        task.form = task.get_form(task.user_solutions)

    if selected_task_id is None and len(tasks) > 0:
        selected_task_id = tasks[0].id
    try:
        selected_task_id = int(selected_task_id)
    except ValueError:
        selected_task_id = None

    return render(request, 'entrance/exam.html', {
        'is_closed': is_closed,
        'entrance_level': base_level,
        'school': request.school,
        'tasks': tasks,
        'is_user_at_maximum_level': upgrades.is_user_at_maximum_level(
            request.school,
            request.user,
            base_level
        ),
        'can_upgrade': upgrades.can_user_upgrade(
            request.school,
            request.user,
            base_level
        ),
        'selected_task_id': selected_task_id
    })


@login_required
def task(request, task_id):
    return exam(request, task_id)


@login_required
@require_POST
def submit(request, task_id):
    entrance_exam = get_object_or_404(models.EntranceExam, school=request.school)
    is_closed = entrance_exam.is_closed()

    task = get_object_or_404(models.EntranceExamTask, pk=task_id)
    if task.exam_id != entrance_exam.id:
        return HttpResponseNotFound()

    ip = ipware.ip.get_ip(request) or ''

    form = task.get_form([], data=request.POST, files=request.FILES)

    # TODO (andgein): extract this logic to models
    if type(task) is models.TestEntranceExamTask:
        if is_closed:
            form.add_error('solution', 'Вступительная работа завершена. Решения больше не принимаются')
        elif form.is_valid():
            solution_text = form.cleaned_data['solution']
            solution = models.TestEntranceExamTaskSolution(
                user=request.user,
                task=task,
                solution=solution_text,
                ip=ip
            )
            solution.save()

            return JsonResponse({'status': 'ok', 'solution_id': solution.id})

        return JsonResponse({'status': 'error', 'errors': form.errors})

    if type(task) is models.FileEntranceExamTask:
        if is_closed:
            form.add_error('solution', 'Вступительная работа завершена. Решения больше не принимаются')
        elif form.is_valid():
            form_file = form.cleaned_data['solution']
            solution_file = sistema.uploads.save_file(
                form_file,
                'entrance-exam-files-solutions'
            )

            solution = models.FileEntranceExamTaskSolution(
                user=request.user,
                task=task,
                solution=solution_file,
                original_filename=form_file.name,
                ip=ip
            )
            solution.save()
            return JsonResponse({'status': 'ok', 'solution_id': solution.id})

        return JsonResponse({'status': 'error', 'errors': form.errors})

    if (type(task) is models.ProgramEntranceExamTask or
       type(task) is models.OutputOnlyEntranceExamTask):
        if is_closed:
            form.add_error('solution', 'Вступительная работа завершена. Решения больше не принимаются')
        elif form.is_valid():
            solution_file = sistema.uploads.save_file(
                form.cleaned_data['solution'],
                'entrance-exam-programs-solutions'
            )

            with transaction.atomic():
                if type(task) is models.ProgramEntranceExamTask:
                    language = form.cleaned_data['language']
                    solution_kwargs = {'language': language}
                else:
                    language = None
                    solution_kwargs = {}

                ejudge_queue_element = modules.ejudge.queue.add_from_file(
                    task.ejudge_contest_id,
                    task.ejudge_problem_id,
                    language,
                    solution_file
                )

                solution = task.solution_class(
                    user=request.user,
                    task=task,
                    solution=solution_file,
                    ejudge_queue_element=ejudge_queue_element,
                    ip=ip,
                    **solution_kwargs
                )
                solution.save()
            return JsonResponse({'status': 'ok', 'solution_id': solution.id})

        return JsonResponse({'status': 'error', 'errors': form.errors})


@login_required
def task_solutions(request, task_id):
    task = get_object_or_404(models.EntranceExamTask, id=task_id)
    solutions = task.solutions.filter(user=request.user).order_by('-created_at')

    if (type(task) is models.ProgramEntranceExamTask or
       type(task) is models.OutputOnlyEntranceExamTask):
        is_checking = any(s.result is None for s in solutions)
        is_passed = any(s.is_checked and s.result.is_success for s in solutions)

        template_name = task.solutions_template_file

        return render(request, 'entrance/exam/' + template_name, {
            'task': task,
            'solutions': solutions,
            'is_checking': is_checking,
            'is_passed': is_passed
        })

    if type(task) is models.FileEntranceExamTask:
        return render(request, 'entrance/exam/_file_solutions.html', {
            'task': task,
            'solution': solutions.first()
        })

    return HttpResponseNotFound()


@login_required
def upgrade_panel(request):
    base_level, _ = get_entrance_level_and_tasks(request.school, request.user)

    return render(request, 'entrance/_exam_upgrade.html', {
        'is_user_at_maximum_level': upgrades.is_user_at_maximum_level(
            request.school,
            request.user,
            base_level
        ),
        'can_upgrade': upgrades.can_user_upgrade(
            request.school,
            request.user,
            base_level
        ),
    })


@login_required
def solution(request, solution_id):
    solution = get_object_or_404(models.FileEntranceExamTaskSolution,
                                 id=solution_id)

    if solution.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden()

    return sistema.helpers.respond_as_attachment(request,
                                                 solution.solution,
                                                 solution.original_filename)


@require_POST
@login_required
@transaction.atomic
def upgrade(request):
    entrance_exam = get_object_or_404(models.EntranceExam, school=request.school)
    is_closed = entrance_exam.is_closed()

    # Not allow to upgrade if exam has been finished already
    if is_closed:
        return redirect(entrance_exam.get_absolute_url())

    base_level = upgrades.get_base_entrance_level(request.school, request.user)

    # We may need to upgrade several times because there are levels with
    # the same sets of tasks
    while upgrades.can_user_upgrade(request.school, request.user):
        maximum_level = upgrades.get_maximum_issued_entrance_level(
            request.school,
            request.user,
            base_level
        )
        next_level = models.EntranceLevel.objects.filter(
            school=request.school,
            order__gt=maximum_level.order
        ).order_by('order').first()

        models.EntranceLevelUpgrade(
            user=request.user,
            upgraded_to=next_level
        ).save()

    return redirect(entrance_exam.get_absolute_url())


def results(request):
    table = EntrancedUsersTable.create(request.school)

    return render(request, 'entrance/results.html', {
        'table': table,
        'school': request.school,
    })
