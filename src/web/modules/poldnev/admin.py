from django.contrib import admin
from django.utils import html

from . import models

class SessionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'poldnev_id',
        'name_as_url',
        'schools_session',
        'verified',
    )

    def name_as_url(self, obj):
        if obj.url:
            return html.format_html('<a href="{}">{}</a>', obj.url, obj.name)
        return None
    name_as_url.short_description = 'Name'
    name_as_url.admin_order_field = 'name'

    search_fields = ('=poldnev_id', '=name')
    ordering = ('-poldnev_id',)

admin.site.register(models.Session, SessionAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'poldnev_id',
        'first_name',
        'middle_name',
        'last_name',
        'user',
        'verified',
        'show_url',
    )

    def show_url(self, obj):
        return html.format_html('<a href="{url}">{url}</a>', url=obj.url)
    show_url.short_description = "URL"

    search_fields = (
        '=poldnev_id',
        'first_name',
        'middle_name',
        'last_name',
    )

admin.site.register(models.Person, PersonAdmin)

class RoleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'session',
        'poldnev_role',
    )

    list_filter = (
        'session',
    )

    search_fields = (
        '=poldnev_role',
    )

    ordering = (
        'session',
        'poldnev_role',
    )

admin.site.register(models.Role, RoleAdmin)

class HistoryEntryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'role',
        'show_url',
    )

    def show_url(self, obj):
        return html.format_html('<a href="{url}">{url}</a>', url=obj.url)
    show_url.short_description = "URL"

    list_filter = (
        'role__session',
    )

    search_fields = (
        'person__first_name',
        'person__middle_name',
        'person__last_name',
    )

    ordering = (
        'person',
        'role__session',
    )

admin.site.register(models.HistoryEntry, HistoryEntryAdmin)
