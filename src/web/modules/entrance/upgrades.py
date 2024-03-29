import modules.topics.models
from sistema.cache import cache
from . import models


# TODO(artemtab): I've made this timeout 10 days long as a workaround for
#     checking 2017. We need to be able to see and export enrolling table
#     without waiting forever. There shouldn't be any harm in doing that,
#     because entrance levels do not change after exam is over.
# TODO(andgein): In 2018 I've reverted timeout back to 30 seconds
@cache(60)
def get_base_entrance_level(school, user):
    override = (models.EntranceLevelOverride.objects
                .filter(school=school, user=user).first())
    if override is not None:
        return override.entrance_level

    return _get_entrance_level_by_limiters(school, user, allow_recommendation_only_limiters=False)


@cache(60)
def get_recommended_entrance_level(school, user):
    return _get_entrance_level_by_limiters(school, user, allow_recommendation_only_limiters=True)


def _get_entrance_level_by_limiters(school, user, allow_recommendation_only_limiters: bool):
    current_limit = models.EntranceLevelLimit(None)
    limiters = school.entrance_level_limiters.all()
    if not allow_recommendation_only_limiters:
        limiters = limiters.filter(is_recommendation_only_limiter=False)
    for limiter in limiters:
        current_limit.update_with_other(limiter.get_limit(user))

    if current_limit.min_level is None:
        # Let's find minimal entrance level for the school
        return school.entrance_levels.order_by('order').first()
    return current_limit.min_level


def get_topics_entrance_level(school, user):
    # Create limiter, but don't save it to database
    # Actually, we could get limiter from the database, but it's not guaranteed
    # that it exists.
    fake_limiter = modules.topics.models.TopicsEntranceLevelLimiter(
        school=school
    )
    return fake_limiter.get_limit(user).min_level


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
        if base_level is None:
            return False

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
