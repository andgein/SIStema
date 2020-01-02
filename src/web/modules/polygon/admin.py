from django.contrib import admin

from . import models


@admin.register(models.Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = (
        'polygon_id',
        'name',
        'owner',
        'revision',
        'latest_package',
    )
    search_fields = ('=polygon_id', 'name')
    ordering = ('-polygon_id',)


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'tag',
    )
    search_fields = ('tag',)

