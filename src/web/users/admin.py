from django.contrib import admin
from hijack.contrib.admin import HijackUserAdminMixin
from reversion.admin import VersionAdmin
from django.utils import translation

from . import models


@admin.register(models.User)
class UserAdmin(HijackUserAdminMixin, VersionAdmin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_active',
        'is_superuser',
        'is_staff',
        # 'hijack_field',
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

    def hijack_button(self, request, obj):
        """
        Russian version of the hijack button is awful ("захватить"),
        so we override the language during the rendering
        """
        cur_language = translation.get_language()
        try:
            translation.activate("en-US")
            return super().hijack_button(request, obj)
        finally:
            translation.activate(cur_language)



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

    autocomplete_fields = (
        'user',
        'poldnev_person',
    )
