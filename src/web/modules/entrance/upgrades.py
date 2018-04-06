import modules.entrance.levels
import modules.topics.entrance.levels
from . import models

# Quick fix to possibly survive high QPS
# TODO: refactor from here
from hashlib import sha1
from django.core.cache import cache as _djcache


def cache(seconds=900):
    """
    Cache the result of a function call for the specified number of seconds,
    using Django's caching mechanism.
    Assumes that the function never returns None (as the cache returns None to indicate a miss), and that the function's result only depends on its parameters.
    Note that the ordering of parameters is important. e.g. myFunction(x = 1, y = 2), myFunction(y = 2, x = 1), and myFunction(1,2) will each be cached separately.

    Usage:

    @cache(600)
    def myExpensiveMethod(parm1, parm2, parm3):
        ....
        return expensiveResult
    """
    def doCache(f):
        def x(*args, **kwargs):
                key = sha1((str(f.__module__) + str(f.__name__) + str(args) + str(kwargs)).encode('utf-8')).hexdigest()
                result = _djcache.get(key)
                if result is None:
                    result = f(*args, **kwargs)
                    _djcache.set(key, result, seconds)
                return result
        return x
    return doCache
# TODO: to here


# TODO(artemtab): I've made this timeout 10 days long as a workaround for
#     checking 2017. We need to be able to see and export enrolling table
#     without waiting forever. There shouldn't be any harm in doing that,
#     because entrance levels do not change after exam is over.
# TODO(andgein): In 2018 I've revered timeout back to 10 minutes
@cache(10 * 60)
def get_base_entrance_level(school, user):
    override = (models.EntranceLevelOverride.objects
                .filter(school=school, user=user).first())
    if override is not None:
        return override.entrance_level

    limiters = [modules.topics.entrance.levels.TopicsEntranceLevelLimiter,
                modules.entrance.levels.AlreadyWasEntranceLevelLimiter,
                modules.entrance.levels.AgeEntranceLevelLimiter,
                modules.entrance.levels.EnrollmentTypeEntranceLevelLimiter,
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

    return not models.EntranceLevel.objects.filter(
        school=school,
        order__gt=max_user_level.order).exists()


# User can upgrade if he hasn't reached the maximum level yet and solved all
# the required tasks.
def can_user_upgrade(school, user, base_level=None):
    if base_level is None:
        base_level = get_base_entrance_level(school, user)
    issued_level = get_maximum_issued_entrance_level(school, user, base_level)

    if is_user_at_maximum_level(school, user, base_level):
        return False

    requirements = models.EntranceLevelUpgradeRequirement.objects.filter(
        base_level=issued_level
    )

    return all(requirement.is_met_by_user(user) for requirement in requirements)


def get_entrance_tasks(school, user, base_level):
    maximum_level = get_maximum_issued_entrance_level(school, user, base_level)

    issued_levels = models.EntranceLevel.objects.filter(
        school=school, order__range=(base_level.order, maximum_level.order))

    issued_tasks = set()
    for level in issued_levels:
        for task in level.tasks.all():
            issued_tasks.add(task)

    return list(sorted(issued_tasks, key=lambda x: x.order))
