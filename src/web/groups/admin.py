from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelFilter,
                               PolymorphicChildModelAdmin)

import sistema.polymorphic
from groups import models


@admin.register(models.AbstractGroup)
class AbstractGroupAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.AbstractGroup
    list_display = ('id', 'school', 'created_by', 'short_name', 'name',
                    'can_be_deleted', )
    list_filter = (('school', admin.RelatedOnlyFieldListFilter), )
    autocomplete_fields = ('created_by',)
    search_fields = (
        '=id',
        'created_by__profile__first_name',
        '=created_by__profile__middle_name',
        '=created_by__profile__last_name',
        'created_by__email',
        'short_name',
        'name',
        'description',
        'school__name',
        'school__full_name',
    )
    ordering = ('-school', 'short_name')


class AbstractGroupChildAdmin(PolymorphicChildModelAdmin):
    autocomplete_fields = AbstractGroupAdmin.autocomplete_fields
    search_fields = AbstractGroupAdmin.search_fields


@admin.register(models.ManuallyFilledGroup)
class ManuallyFilledGroupAdmin(AbstractGroupChildAdmin):
    base_model = models.ManuallyFilledGroup


@admin.register(models.GroupInGroupMembership)
@admin.register(models.UserInGroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'member')
    list_filter = (('group', admin.RelatedOnlyFieldListFilter), )
    autocomplete_fields = ('group', 'added_by', 'member')


@admin.register(models.GroupAccess)
class GroupAccessAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.GroupAccess
    list_display = ('id', 'get_description_html', 'to_group', 'access_type',
                    'created_by', 'created_at')
    list_display_links = ('id', 'get_description_html')
    list_filter = ('to_group__school',
                   'access_type',
                   PolymorphicChildModelFilter)
    autocomplete_fields = ('created_by', 'to_group')
    ordering = ('to_group__school', '-created_at')


@admin.register(models.GroupAccessForUser)
class GroupAccessForUserAdmin(PolymorphicChildModelAdmin):
    base_model = models.GroupAccess
    autocomplete_fields = GroupAccessAdmin.autocomplete_fields + ('user',)


@admin.register(models.GroupAccessForGroup)
class GroupAccessForGroupAdmin(PolymorphicChildModelAdmin):
    base_model = models.GroupAccess
    autocomplete_fields = GroupAccessAdmin.autocomplete_fields + ('group',)
