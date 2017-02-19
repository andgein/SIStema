from django.contrib import admin

from . import models


class StudyResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'user',
        'parallel',
        'theory',
        'practice',
    )
    list_filter = (
        'school',
        'parallel',
        'theory',
        'practice',
    )
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
    )

admin.site.register(models.StudyResult, StudyResultAdmin)
