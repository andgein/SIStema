import modules.entrance.levels
import modules.topics.entrance.levels
from . import models


def get_base_entrance_level(school, user):
    limiters = [modules.topics.entrance.levels.TopicsEntranceLevelLimiter,
                modules.entrance.levels.AlreadyWasEntranceLevelLimiter,
                modules.entrance.levels.AgeEntranceLevelLimiter
                ]

    current_limit = modules.entrance.levels.EntranceLevelLimit(None)
    for limiter in limiters:
        current_limit.update_with_other(limiter(school).get_limit(user))

    return current_limit.min_level


def get_maximum_issued_entrance_level(school, user, base_level):
    user_upgrades = models.EntranceLevelUpgrade.objects.filter(user=user, upgraded_to__school=school)
    maximum_upgrade = user_upgrades.order_by('-upgraded_to__order').first()
    if maximum_upgrade is None:
        return base_level

    maximum_user_level = maximum_upgrade.upgraded_to
    if maximum_user_level > base_level:
        return maximum_user_level
    return base_level


def is_user_at_maximum_level(school, user, base_level):
    max_user_level = get_maximum_issued_entrance_level(school, user, base_level)

    return not models.EntranceLevel.objects.filter(order__gt=max_user_level.order).exists()


# User can upgrade if he hasn't reached the maximum level yet and solved all
# the required tasks.
def can_user_upgrade(school, user):
    base_level = get_base_entrance_level(school, user)
    issued_level = get_maximum_issued_entrance_level(school, user, base_level)

    if is_user_at_maximum_level(school, user, base_level):
        return False

    requirements = models.EntranceLevelUpgradeRequirement.objects.filter(base_level=issued_level)

    return all(requirement.get_child_object().is_met_by_user(user)
               for requirement in requirements)


def get_entrance_tasks(school, user, base_level):
    maximum_level = get_maximum_issued_entrance_level(school, user, base_level)

    issued_levels = models.EntranceLevel.objects.filter(order__range=(base_level.order, maximum_level.order))

    issued_tasks = set()
    for level in issued_levels:
        for task in level.tasks.all().order_by('order'):
            issued_tasks.add(task)

    return list(issued_tasks)