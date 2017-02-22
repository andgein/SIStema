from django.contrib import admin

from reversion.admin import VersionAdmin

from . import models


class SchoolAdmin(VersionAdmin):
    list_display = (
        'id',
        'is_public',
        'short_name',
        'name',
        'full_name'
    )


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


admin.site.register(models.School, SchoolAdmin)
admin.site.register(models.Session, SessionAdmin)
admin.site.register(models.Parallel, ParallelAdmin)
