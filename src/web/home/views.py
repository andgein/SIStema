from django import shortcuts
from django.contrib.auth.decorators import login_required
import django.urls

from sistema.staff import only_staff
import schools.models


def home(request):
    if not request.user.is_authenticated:
        return shortcuts.redirect('account_login')

    if request.user.is_staff:
        return shortcuts.redirect(django.urls.reverse('staff'))

    return shortcuts.redirect(django.urls.reverse('user'))


@only_staff
def staff(request):
    current_school = schools.models.School.get_current_school()

    return shortcuts.redirect(current_school.get_staff_url())


@login_required
def user(request):
    current_school = schools.models.School.get_current_school()

    return shortcuts.redirect(current_school.get_user_url())
