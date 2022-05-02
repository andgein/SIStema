from django.contrib import admin

from modules.study_results import models


@admin.register(models.StudyResult)
class StudyResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_parallel',
        'school_participant',
        'theory',
        'practice',
    )
    list_filter = (
        'school_participant__school',
        'school_participant__parallel',
        'theory',
        'practice',
    )
    autocomplete_fields = ('school_participant',)
    search_fields = (
        'school_participant__user__profile__first_name',
        'school_participant__user__profile__last_name',
        'school_participant__user__first_name',
        'school_participant__user__last_name',
        'school_participant__user__username',
    )

    def get_parallel(self, result):
        return result.school_participant.parallel
    get_parallel.short_description = 'parallel'
