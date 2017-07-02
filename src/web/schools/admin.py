from django.contrib import admin

from reversion.admin import VersionAdmin

from schools import models
import sistema.admin


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


@admin.register(models.Parallel)
class ParallelAdmin(sistema.admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'short_name',
        'name',
    )

    list_filter = (
        'school',
    )


@admin.register(models.SchoolParticipant)
class SchoolParticipantAdmin(sistema.admin.ModelAdmin):
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
