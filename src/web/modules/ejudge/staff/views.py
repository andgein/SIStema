import collections

import django.shortcuts
from django.db.models import F, Count

import sistema.staff
import modules.ejudge.models as ejudge_models
import modules.entrance.models as entrance_models


def get_program_tasks(school):
    program_tasks = (entrance_models.ProgramEntranceExamTask.objects
        .filter(exam__school=school)
        .order_by('order'))
    return program_tasks


def count_stats(school):
    program_tasks = get_program_tasks(school).prefetch_related(
        'solutions__programentranceexamtasksolution__ejudge_queue_element')
    # Fetch result and status for submission
    annotated_tasks = program_tasks.annotate(
        status=F('solutions__programentranceexamtasksolution'
                 '__ejudge_queue_element__status'),
        result=F('solutions__programentranceexamtasksolution'
                 '__ejudge_queue_element__submission__result__result'),
    )
    # For each task count submissions with different ejudge results
    queue_stats = (annotated_tasks
        .values('title', 'status')
        .annotate(count=Count('solutions')))
    submission_stats = (annotated_tasks
        .values('title', 'result')
        .annotate(count=Count('solutions'), status=F('result')))
    # Write django.choices in readable form
    for entry in queue_stats:
        if entry['status'] is None:
            continue
        entry['status'] = (
            ejudge_models.QueueElement.Status.values[entry['status']])

    for entry in submission_stats:
        if entry['status'] is None:
            continue
        entry['status'] = (
            ejudge_models.CheckingResult.Result.values[entry['status']])

    return queue_stats, submission_stats


def get_rows(stats, tasks, headers):
    a = collections.defaultdict(int)
    for stat in stats:
        a[stat['status'], stat['title']] = stat['count']
    return [{'task': task, 'counts': [a[header, task] for header in headers]}
            for task in tasks]


@sistema.staff.only_staff
def show_ejudge_stats(request):
    queue_stats, submission_stats = count_stats(request.school)
    tasks = get_program_tasks(request.school).values_list('title', flat=True)
    statuses = list(ejudge_models.QueueElement.Status.values.values())

    existing_results = set(x['status']
        for x in submission_stats
        if x['status'] is not None)
    results = [result
        for result in ejudge_models.CheckingResult.Result.values.values()
        if result in existing_results]

    return django.shortcuts.render(
        request,
        'ejudge/staff/ejudge_stats.html',
        {
            'queue_stats': get_rows(queue_stats, tasks, statuses),
            'submission_stats': get_rows(submission_stats, tasks, results),
            'statuses': statuses,
            'results': results,
        }
    )
