from django.contrib import admin

from modules.study_results import models


@admin.register(models.StudyResult)
class StudyResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school_participant__school',
        'school_participant__parallel',
        'school_participant__user',
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
