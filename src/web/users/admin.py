from django.contrib import admin

from hijack_admin.admin import HijackUserAdminMixin
from reversion.admin import VersionAdmin

from . import models


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
        'is_email_confirmed',
        'hijack_field',
    )

    list_filter = (
        'is_superuser',
        'is_staff',
        'is_email_confirmed',
        'is_active',
    )

    search_fields = (
        '=username',
        '=first_name',
        '=last_name',
        '=email',
    )


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

admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserProfile, UserProfileAdmin)
