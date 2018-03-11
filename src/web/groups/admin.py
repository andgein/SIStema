from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelFilter,
                               PolymorphicChildModelAdmin)

import sistema.polymorphic
import users.admin
from groups import models


@admin.register(models.AbstractGroup)
class AbstractGroupAdmin(users.admin.UserAutocompleteModelAdminMixIn, sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.AbstractGroup
    list_display = ('id', 'school', 'created_by', 'short_name', 'name',
                    'can_be_deleted', )
    list_filter = (('school', admin.RelatedOnlyFieldListFilter), )
    search_fields = (
        '=id',
        'created_by__profile__first_name',
        '=created_by__profile__middle_name',
        '=created_by__profile__last_name',
        'created_by__email',
        'short_name',
        'name',
        'description'
    )
    ordering = ('-school', 'short_name')


@admin.register(models.ManuallyFilledGroup)
class ManuallyFilledGroupAdmin(PolymorphicChildModelAdmin):
    base_model = models.ManuallyFilledGroup


@admin.register(models.GroupInGroupMembership)
@admin.register(models.UserInGroupMembership)
class GroupMembershipAdmin(users.admin.UserAutocompleteModelAdminMixIn,
                           admin.ModelAdmin):
    list_display = ('id', 'group', 'member')
    list_filter = (('group', admin.RelatedOnlyFieldListFilter), )


@admin.register(models.GroupAccess)
class GroupAccessAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.GroupAccess
    list_display = ('id', 'get_description_html', 'to_group', 'access_type',
                    'created_by', 'created_at')
    list_display_links = ('id', 'get_description_html')
    list_filter = ('to_group__school',
                   'access_type',
                   PolymorphicChildModelFilter)
    ordering = ('to_group__school', '-created_at')


@admin.register(models.GroupAccessForUser)
@admin.register(models.GroupAccessForGroup)
class GroupAccessChildAdmin(users.admin.UserAutocompleteModelAdminMixIn,
                            PolymorphicChildModelAdmin):
    base_model = models.GroupAccess

