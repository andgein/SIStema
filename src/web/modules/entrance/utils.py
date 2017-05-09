from modules.entrance import models
import users.models


def get_enrolling_users(school):
    return (users.models.User.objects
            .filter(entrance_statuses__school=school)
            .exclude(entrance_statuses__status=
                     models.EntranceStatus.Status.NOT_PARTICIPATED))


def get_enrolling_users_ids(school):
    return models.EntranceStatus.objects.filter(
        school=school
    ).exclude(
        status=models.EntranceStatus.Status.NOT_PARTICIPATED
    ).values_list('user_id', flat=True)
