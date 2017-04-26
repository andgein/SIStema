from constance import config
from django import shortcuts

import schools.models


def home(request):
    if not request.user.is_authenticated:
        return shortcuts.redirect('account_login')

    # TODO(Artem Tabolin): That's the wrong way to get the current school. We
    #     should introduce some global settings module to hold its value.
    short_name = config.SISTEMA_CURRENT_SCHOOL_SHORT_NAME
    current_school = schools.models.School.objects.get(short_name=short_name)

    return shortcuts.redirect(current_school)
