import collections
import operator

from django.http import Http404
from django.shortcuts import render

import sistema.staff
import groups.decorators
# TODO (andgein): Don't use group from another module
import modules.entrance.groups as entrance_groups
import modules.topics.models as topics_models


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.ADMINS)
def info(request):
    return render(request, 'topics/staff/info.html', {})


@sistema.staff.only_staff
@groups.decorators.only_for_groups(entrance_groups.ADMINS)
def preview(request):
    questionnaire = request.school.topicquestionnaire
    if questionnaire is None:
        raise Http404()

    statuses = topics_models.UserQuestionnaireStatus.objects.filter(
        questionnaire__school=request.school,
        status=topics_models.UserQuestionnaireStatus.Status.FINISHED
    ).select_related('user')
    users = sorted([status.user for status in statuses], key=operator.attrgetter('id'))

    levels = []
    users_by_level = collections.defaultdict(list)
    for user in users:
        level = topics_models.TopicsEntranceLevelLimit.compute_level(user=user, questionnaire=questionnaire)
        levels.append((user, level))
        users_by_level[level].append(user)

    return render(request, 'topics/staff/preview.html', {
        'levels': levels,
        # Sort levels by its order
        'users_by_level': sorted(users_by_level.items(), key=lambda p: p[0].order),
    })
