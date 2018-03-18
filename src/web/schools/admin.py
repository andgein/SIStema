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

    ordering = ('-year', '-name')


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

    ordering = ('-school__year', '-school__name', '-start_date')

    search_fields = ('school__name', 'name')


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

    ordering = ('-school__year', '-school__name', 'name')

    autocomplete_fields = ('sessions',)

    search_fields = ('=school__year', 'school__name', 'short_name', 'name')


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
        'parallel__name',
        'session__name',
        'session__school__name',
    )

    # Make admin invisible. It's exposed through inline parallel admin.
    def get_model_perms(self, request):
        return {}


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
    autocomplete_fields = ('user', 'parallel')
