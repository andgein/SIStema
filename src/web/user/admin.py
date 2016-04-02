from django.contrib import admin

from hijack.admin import HijackUserAdminMixin
from reversion.admin import VersionAdmin

from . import models


class UserAdmin(VersionAdmin, HijackUserAdminMixin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_superuser',
        'is_staff',
        'is_email_confirmed',
        'hijack_field',
    )


admin.site.register(models.User, UserAdmin)
