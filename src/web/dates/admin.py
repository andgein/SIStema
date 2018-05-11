from django.contrib import admin

from dates import models


class GroupKeyDateExceptionInline(admin.StackedInline):
    model = models.GroupKeyDateException
    extra = 0
    autocomplete_fields = ('group',)


class UserKeyDateExceptionInline(admin.StackedInline):
    model = models.UserKeyDateException
    extra = 0
    autocomplete_fields = ('user',)


@admin.register(models.KeyDate)
class KeyDateAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'datetime',
        'name',
    )
    list_filter = ('school',)
    inlines = (GroupKeyDateExceptionInline, UserKeyDateExceptionInline)
    search_fields = ('=id', 'name', 'school__name', 'datetime')
