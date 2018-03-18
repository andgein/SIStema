from django.contrib import admin

from modules.study_results import models


@admin.register(models.StudyResult)
class StudyResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school_participant',
        'theory',
        'practice',
    )
    list_filter = (
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
