from django.contrib import admin
import django.forms

from dal import autocomplete
from hijack_admin.admin import HijackUserAdminMixin
from reversion.admin import VersionAdmin

from users import models
import sistema.admin


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


sistema.admin.register_autocomplete_field_for_foreign_key(
    models.User,
    url='users_admin:user-autocomplete',
    placeholder='Выберите пользователя',
)
