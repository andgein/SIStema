from django.contrib import admin

from hijack_admin.admin import HijackUserAdminMixin
from reversion.admin import VersionAdmin

from sistema.admin import AutocompleteModelAdminMixIn
from . import models


@admin.register(models.User)
class UserAdmin(VersionAdmin, HijackUserAdminMixin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_active',
        'is_superuser',
        'is_staff',
        'hijack_field',
    )

    list_filter = (
        'is_superuser',
        'is_staff',
        'is_active',
    )

    search_fields = (
        '=id',
        'username',
        'first_name',
        'last_name',
        'profile__first_name',
        'profile__middle_name',
        'profile__last_name',
        'email',
    )


@admin.register(models.UserProfile)
class UserProfileAdmin(VersionAdmin):
    list_display = (
        'user_id',
        'last_name',
        'first_name',
        'middle_name',
    )

    search_fields = (
        '=first_name',
        '=middle_name',
        '=last_name',
    )


class UserAutocompleteModelAdminMixIn(AutocompleteModelAdminMixIn):
    """ Add UserAutocompleteModelAdminMixIn as first base class of your
        admin class and all foreign keys to User class will be rendered
        via Select2 with autocomplete """

    object_model = models.User
    url = 'user-autocomplete'
    placeholder = 'Выберите пользователя'
