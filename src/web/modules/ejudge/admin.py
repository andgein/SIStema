from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from . import models


@admin.register(models.ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'name', 'ejudge_id')

    search_fields = ('=id', 'name', 'short_name')


@admin.register(models.QueueElement)
class QueueElementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ejudge_contest_id',
        'ejudge_problem_id',
        'submission_link',
        'language',
        'status',
        'updated_at',
    )

    list_filter = (
        'status',
        'language',
        'ejudge_contest_id',
        'ejudge_problem_id',
    )

    autocomplete_fields = ('submission', 'language')

    search_fields = ('=id',)

    @staticmethod
    def submission_link(obj):
        if obj.submission is None:
            return ''
        url = reverse('admin:ejudge_submission_change',
                      args=[obj.submission.id])
        return mark_safe('<a href="{}">{}</a>'.format(url, obj.submission))


@admin.register(models.SolutionCheckingResult)
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
    search_fields = ('=id',)


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ejudge_contest_id',
        'ejudge_submit_id',
        'result_link',
        'updated_at',
    )

    list_filter = ('result__result', 'ejudge_contest_id',)
    autocomplete_fields = ('result',)
    search_fields = ('=id', '=ejudge_submit_id',)

    def result_link(self, obj):
        url = reverse('admin:ejudge_solutioncheckingresult_change',
                      args=[obj.result.id])
        return mark_safe('<a href="{}">{}</a>'.format(url, obj.result))


admin.site.register(models.TestCheckingResult)
