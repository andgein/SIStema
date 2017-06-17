from django.contrib import admin

from reversion.admin import VersionAdmin

from . import models


@admin.register(models.School)
class SchoolAdmin(VersionAdmin):
    list_display = (
        'id',
        'is_public',
        'short_name',
        'name',
        'full_name'
    )


@admin.register(models.Session)
class SessionAdmin(VersionAdmin):
    list_display = (
        'id',
        'school',
        'short_name',
        'name',
    )

    list_filter = (
        'school',
    )


class GroupInline(admin.TabularInline):
    model = models.Group
    extra = 0


@admin.register(models.Parallel)
class ParallelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'short_name',
        'name',
    )

    list_filter = (
        'school',
    )

    inlines = (
        GroupInline,
    )


@admin.register(models.SchoolParticipant)
class SchoolParticipantAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'user',
        'parallel',
    )
    list_filter = (
        'school',
        'parallel',
    )
