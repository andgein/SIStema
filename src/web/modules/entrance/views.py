import operator

import django.urls
import ipware.ip
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Min
from django.http.response import (HttpResponseNotFound,
                                  JsonResponse,
                                  HttpResponseForbidden)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

import frontend.icons
import frontend.table
import modules.ejudge.queue
import sistema.helpers
import sistema.uploads
import users.models
from frontend.table.utils import TableDataSource
from . import forms
from . import models
from . import upgrades


def get_entrance_level_selected_by_user(school, user, base_level):
    last_selected_level = (
        models.SelectedEntranceLevel.objects
            .filter(school=school, user=user)
            .order_by('-created_at')
            .first()
    )
    if last_selected_level is None:
        return None

    level = last_selected_level.level
    if base_level > level:
        level = base_level

    return level


def get_entrance_level_and_tasks(school, user):
    level = upgrades.get_base_entrance_level(school, user)
    if not hasattr(school, 'entrance_exam') or not school.entrance_exam or level is None:
        # No exam or no levels — no tasks, sorry
        return level, []

    if level.id is None:
        # Sometimes we have fake "maximal" level which is not exist in database.
        # In this case user has no tasks
        return level, []

    if school.entrance_exam.can_participant_select_entrance_level:
        selected_level = get_entrance_level_selected_by_user(school, user, level)
        if selected_level is not None and selected_level >= level:
            level = selected_level
        tasks = list(sorted(level.tasks.select_related('category', 'exam', 'exam__school').all(), key=lambda x: x.order))
    else:
        tasks = upgrades.get_entrance_tasks(school, user, level)

    # Some tasks may have a filter, which specifies the group of students who can see this task
    tasks = [
        task for task in tasks
        if task.visible_only_for_group is None or task.visible_only_for_group.is_user_in_group(user)
    ]

    return level, tasks


class EntrancedUsersTable(frontend.table.Table):
    index = frontend.table.IndexColumn(verbose_name='')

    name = frontend.table.Column(
        accessor='get_full_name',
        verbose_name='Имя',
        order_by=('profile.last_name',
                  'profile.first_name'),
        search_in=('profile.first_name',
                   'profile.last_name'))

    city = frontend.table.Column(
        accessor='profile__city',
        orderable=True,
        searchable=True,
        verbose_name='Город')

    school_and_class = frontend.table.Column(
        accessor='profile',
        search_in='profile.school_name',
        verbose_name='Школа и класс')

    session = frontend.table.Column(
        accessor='entrance_statuses',
        verbose_name='Смена')

    parallel = frontend.table.Column(
        accessor='entrance_statuses',
        verbose_name='Параллель')

    enrolled_status = frontend.table.Column(
        empty_values=(),
        verbose_name='Статус')

    class Meta:
        icon = frontend.icons.FaIcon('check')
        # TODO: title depending on school
        title = 'Поступившие'
        pagination = False

    def __init__(self, school, *args, **kwargs):
        qs = users.models.User.objects.filter(
            entrance_statuses__school=school,
            entrance_statuses__status=models.EntranceStatus.Status.ENROLLED,
            entrance_statuses__is_status_visible=True,
        ).annotate(
            min_session=Min('entrance_statuses__sessions_and_parallels__session__name'),
            min_parallel=Min('entrance_statuses__sessions_and_parallels__parallel__name')
        ).order_by(
            'min_session',
            'min_parallel',
            'profile__last_name',
            'profile__first_name',
        ).select_related('profile').prefetch_related(
            Prefetch(
                'entrance_statuses',
                models.EntranceStatus.objects.filter(school=school)),
            Prefetch(
                'absence_reasons',
                models.AbstractAbsenceReason.objects.filter(school=school)),
        )

        super().__init__(
            qs,
            django.urls.reverse('school:entrance:results_data',
                                args=[school.short_name]),
            *args, **kwargs)

    def render_school_and_class(self, value):
        parts = []
        if value.school_name:
            parts.append(value.school_name)
        if value.current_class is not None:
            parts.append(str(value.current_class) + ' класс')
        return ', '.join(parts)

    def render_session(self, value):
        # TODO: will it be filtered?
        status = value.get()
        sessions_and_parallels = status.sessions_and_parallels.all()
        selected_session = sessions_and_parallels.filter(selected_by_user=True).first()
        if selected_session is not None:
            return selected_session.session.name if selected_session.session else ''
        return ', '.join(set(
            sessions_and_parallels
                .filter(session__isnull=False)
                .order_by('session_id')
                .values_list('session__name', flat=True)
        ))

    def render_parallel(self, value):
        # TODO: will it be filtered?
        status = value.get()
        sessions_and_parallels = status.sessions_and_parallels.all()
        selected_parallel = sessions_and_parallels.filter(selected_by_user=True).first()
        if selected_parallel is not None:
            return selected_parallel.parallel.name if selected_parallel.parallel else ''
        return ', '.join(set(
            sessions_and_parallels
                .filter(parallel__isnull=False)
                .order_by('parallel_id')
                .values_list('parallel__name', flat=True)
        ))

    def render_enrolled_status(self, record):
        absence_reasons = record.absence_reasons.all()
        absence_reason = absence_reasons[0] if absence_reasons else None
        if absence_reason is not None:
            return str(absence_reason)

        entrance_status = record.entrance_statuses.get()
        if not entrance_status.is_approved:
            return 'Участие не подтверждено'

        return ''


@login_required
def exam(request, selected_task_id=None):
    entrance_exam = get_object_or_404(
        models.EntranceExam,
        school=request.school
    )
    is_closed = entrance_exam.is_closed(request.user)

    level, tasks = get_entrance_level_and_tasks(request.school, request.user)

    # Order task by type and order
    tasks = sorted(tasks, key=lambda t: (t.type_title, t.order))
    for task in tasks:
        task.user_solutions = list(
            task.solutions.filter(user=request.user).order_by('-created_at'))
        task.is_accepted = task.is_accepted_for_user(request.user)
        task.is_solved = task.is_solved_by_user(request.user)
        task.form = task.get_form_for_user(request.user)

    if selected_task_id is None and len(tasks) > 0:
        selected_task_id = tasks[0].id
    try:
        selected_task_id = int(selected_task_id)
    except (ValueError, TypeError):
        selected_task_id = None

    categories = list(sorted(
        {task.category for task in tasks},
        key=operator.attrgetter('order'),
    ))
    for category in categories:
        category.is_started = category.is_started_for_user(request.user)
        category.is_finished = category.is_finished_for_user(request.user)
    categories_with_tasks = [
        (category, [task for task in tasks if task.category == category])
        for category in categories
    ]

    return render(request, 'entrance/exam.html', {
        'is_closed': is_closed,
        'entrance_level': level,
        'school': request.school,
        'categories_with_tasks': categories_with_tasks,
        'can_select_entrance_level': entrance_exam.can_participant_select_entrance_level,
        'is_user_at_maximum_level': upgrades.is_user_at_maximum_level(
            request.school,
            request.user,
            level
        ),
        'can_upgrade': not is_closed and upgrades.can_user_upgrade(
            request.school,
            request.user,
            level
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

    task = get_object_or_404(models.EntranceExamTask, pk=task_id)
    if task.exam_id != entrance_exam.id:
        return HttpResponseNotFound()

    is_closed = (
        entrance_exam.is_closed(request.user) or
        task.category.is_finished_for_user(request.user))

    ip, _ = ipware.ip.get_client_ip(request)
    if not ip:
        ip = ''

    form = task.get_form_for_user(request.user, data=request.POST, files=request.FILES)

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

    if isinstance(task, models.EjudgeEntranceExamTask):
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

    if isinstance(task, models.EjudgeEntranceExamTask):
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
    is_closed = entrance_exam.is_closed(request.user)

    # Not allow to upgrade if exam has been finished already
    # Also not allow to upgrade if exam deny upgrades, because users can select
    # entrance levels for themselves.
    if is_closed or entrance_exam.can_participant_select_entrance_level:
        return redirect(entrance_exam.get_absolute_url())

    base_level = upgrades.get_base_entrance_level(request.school, request.user)
    if base_level is None:
        # No levels at all
        return redirect(entrance_exam.get_absolute_url())

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
    table = EntrancedUsersTable(request.school)
    frontend.table.RequestConfig(request).configure(table)
    return render(request, 'entrance/results.html', {
        'table': table,
        'school': request.school,
    })


@cache_page(5 * 60)
def results_data(request):
    table = EntrancedUsersTable(request.school)
    return TableDataSource(table).get_response(request)


@require_POST
@login_required
def select_entrance_level(request, step_id):
    get_object_or_404(
        models.SolveExamEntranceStep,
        id=step_id, school=request.school
    )
    step_url = reverse('school:user', args=(request.school.short_name, )) + '#entrance-step-' + str(step_id)

    entrance_exam = get_object_or_404(models.EntranceExam, school=request.school)
    if entrance_exam.is_closed(request.user) or not entrance_exam.can_participant_select_entrance_level:
        return redirect(step_url)

    levels = list(request.school.entrance_levels.order_by('order').all())
    base_level = upgrades.get_base_entrance_level(request.school, request.user)
    if base_level is None:
        # No levels at all
        return redirect(step_url)
    form = forms.SelectEntranceLevelForm(levels, base_level, data=request.POST)

    if form.is_valid():
        if form.cleaned_data['level'] == '':
            return redirect(step_url)
        models.SelectedEntranceLevel.objects.create(
            school=request.school,
            user=request.user,
            level_id=form.cleaned_data['level']
        )
    else:
        # TODO (andgein): show error if form is not valid
        raise ValueError('Errors: ' + ', '.join(map(str, form.errors)))
    return redirect(step_url)


@require_POST
@login_required
def set_enrollment_type(request, step_id):
    step = get_object_or_404(
        models.SelectEnrollmentTypeEntranceStep,
        id=step_id, school=request.school
    )
    form = forms.SelectEnrollmentTypeForm(
        step.enrollment_types.all(),
        data=request.POST
    )
    if form.is_valid():
        enrollment_type = models.EnrollmentType.objects.get(
            pk=form.cleaned_data['enrollment_type']
        )
        models.SelectedEnrollmentType.objects.update_or_create(
            user=request.user,
            step=step,
            defaults={
                'enrollment_type': enrollment_type,
                'is_moderated': not enrollment_type.needs_moderation,
                'is_approved': not enrollment_type.needs_moderation,
                'entrance_level': None
            }
        )
    else:
        # TODO (andgein): show error if form is not valid
        raise ValueError('Errors: ' + ', '.join(map(str, form.errors)))
    return redirect('school:user', request.school.short_name)


@require_POST
@login_required
def reset_enrollment_type(request, step_id):
    step = get_object_or_404(
        models.SelectEnrollmentTypeEntranceStep,
        id=step_id, school=request.school
    )
    models.SelectedEnrollmentType.objects.filter(
        user=request.user,
        step=step
    ).delete()

    return redirect('school:user', request.school.short_name)


@require_POST
@login_required
def select_session_and_parallel(request, step_id):
    get_object_or_404(models.ResultsEntranceStep, id=step_id, school=request.school)
    entrance_status = models.EntranceStatus.get_visible_status(request.school, request.user)
    if not entrance_status.is_enrolled:
        return HttpResponseNotFound()
    form = forms.SelectSessionAndParallelForm(
        entrance_status.sessions_and_parallels.all(),
        data=request.POST
    )
    if form.is_valid():
        selected = models.EnrolledToSessionAndParallel.objects.get(
            pk=form.cleaned_data['session_and_parallel']
        )
        with transaction.atomic():
            selected.select_this_option()
            entrance_status.approve()
    else:
        # TODO (andgein): show error if form is not valid
        raise ValueError('Errors: ' + ', '.join(map(str, form.errors)))
    return redirect('school:user', request.school.short_name)


@require_POST
@login_required
def reset_session_and_parallel(request, step_id):
    step = get_object_or_404(models.ResultsEntranceStep, id=step_id, school=request.school)
    entrance_status = models.EntranceStatus.get_visible_status(request.school, request.user)
    if not entrance_status.is_enrolled:
        return HttpResponseNotFound()

    if step.available_to_time and step.available_to_time.passed_for_user(request.user):
        return redirect('school:user', request.school.short_name)

    with transaction.atomic():
        entrance_status.sessions_and_parallels.update(selected_by_user=False)
        entrance_status.remove_approving()
    return redirect('school:user', request.school.short_name)


@require_POST
@login_required
def approve_enrollment(request, step_id):
    get_object_or_404(models.ResultsEntranceStep, id=step_id, school=request.school)
    entrance_status = models.EntranceStatus.get_visible_status(request.school, request.user)
    if not entrance_status.is_enrolled:
        return HttpResponseNotFound()

    if entrance_status.sessions_and_parallels.count() != 1:
        return HttpResponseNotFound()

    with transaction.atomic():
        entrance_status.sessions_and_parallels.update(selected_by_user=True)
        entrance_status.approve()
    return redirect('school:user', request.school.short_name)


@require_POST
@login_required
def reject_participation(request, step_id):
    get_object_or_404(models.ResultsEntranceStep, id=step_id, school=request.school)
    entrance_status = models.EntranceStatus.get_visible_status(request.school, request.user)
    if not entrance_status.is_enrolled:
        return HttpResponseNotFound()

    models.RejectionAbsenceReason.objects.create(
        school=request.school,
        user=request.user,
        created_by=request.user,
    )
    return redirect('school:user', request.school.short_name)
