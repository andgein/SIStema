from django.contrib import admin

from . import models


class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'name', 'ejudge_id')

admin.site.register(models.ProgrammingLanguage, ProgrammingLanguageAdmin)


class QueueElementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ejudge_contest_id',
        'ejudge_problem_id',
        'submission',
        'language',
        'status',
    )

    list_filter = (
        'status',
        'language',
        'ejudge_contest_id',
        'ejudge_problem_id',
    )

    search_fields = ('id',)

admin.site.register(models.QueueElement, QueueElementAdmin)


class SolutionCheckingResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'result',
        'failed_test',
        'score',
        'max_possible_score',
        'time_elapsed',
        'memory_consumed',
    )

    list_filter = ('result',)

admin.site.register(models.SolutionCheckingResult, SolutionCheckingResultAdmin)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ejudge_contest_id',
        'ejudge_submit_id',
        'result',
    )

    list_filter = ('result__result', 'ejudge_contest_id',)
    search_fields = ('ejudge_submit_id',)

admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.TestCheckingResult)
