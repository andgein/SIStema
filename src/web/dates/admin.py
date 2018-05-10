from django.contrib import admin

from dates import models


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
    inlines = (UserKeyDateExceptionInline,)
    search_fields = ('=id', 'name', 'school__name', 'datetime')
