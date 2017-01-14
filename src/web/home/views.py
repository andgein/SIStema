from django import conf
from django import shortcuts

import schools.models


def home(request):
    if not request.user.is_authenticated():
        return shortcuts.redirect('users:login')

    if not request.user.is_email_confirmed:
        return shortcuts.redirect('users:complete')

    # TODO(Artem Tabolin): That's the wrong way to get the current school. We
    #     should introduce some global settings module to hold its value.
    short_name = conf.settings.CURRENT_SCHOOL_SHORT_NAME
    current_school = schools.models.School.objects.get(short_name=short_name)

    return shortcuts.redirect(current_school)
