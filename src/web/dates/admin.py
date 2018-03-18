from django.contrib import admin

from dates import models


class KeyDateExceptionInline(admin.StackedInline):
    model = models.KeyDateException
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
    inlines = (KeyDateExceptionInline,)
    search_fields = ('=id', 'name', 'school__name', 'datetime')
