from django.contrib import admin
from django.utils import html

from . import models


@admin.register(models.Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        'poldnev_id',
        'name_as_url',
        'schools_session',
        'verified',
    )
    autocomplete_fields = ('schools_session',)

    search_fields = ('=poldnev_id', 'name')
    ordering = ('-poldnev_id',)

    def name_as_url(self, obj):
        if obj.url:
            return html.format_html('<a href="{}">{}</a>', obj.url, obj.name)
        return None
    name_as_url.short_description = 'Name'
    name_as_url.admin_order_field = 'name'


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'poldnev_id',
        'first_name',
        'middle_name',
        'last_name',
        'user',
        'verified',
        'show_url',
    )
    autocomplete_fields = ('user',)
    search_fields = (
        '=poldnev_id',
        'first_name',
        'middle_name',
        'last_name',
    )

    def show_url(self, obj):
        return html.format_html('<a href="{url}">{url}</a>', url=obj.url)
    show_url.short_description = "URL"



@admin.register(models.Parallel)
class ParallelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'session',
        'name',
        'schools_parallel',
    )

    list_filter = ('session',)
    autocomplete_fields = ('session', 'schools_parallel')
    search_fields = ('=name', 'session__name')
    ordering = ('session', 'name',)


@admin.register(models.StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'parallel',
        'name',
    )

    list_filter = ('parallel__session',)
    autocomplete_fields = ('parallel', 'schools_group')
    search_fields = ('name', 'parallel__name', 'parallel__session__name')
    ordering = ('parallel', 'name',)


@admin.register(models.HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'session',
        'study_group',
        'role',
        'show_url',
    )

    def show_url(self, obj):
        return html.format_html('<a href="{url}">{url}</a>', url=obj.url)
    show_url.short_description = "URL"

    list_filter = (
        'session',
    )

    autocomplete_fields = ('person', 'session', 'study_group')

    search_fields = (
        'person__first_name',
        'person__middle_name',
        'person__last_name',
    )

    ordering = (
        'person',
        'session',
    )
