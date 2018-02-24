from django.contrib import admin
from django.urls import reverse
import django.forms

from dal import autocomplete

from . import models


@admin.register(models.ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'name', 'ejudge_id')


class QueueElementAdminForm(django.forms.ModelForm):
    class Meta:
        model = models.QueueElement
        fields = ('__all__')
        widgets = {
            'submission': autocomplete.ModelSelect2(
                url='ejudge:admin:submission-autocomplete')
        }


@admin.register(models.QueueElement)
class QueueElementAdmin(admin.ModelAdmin):
    form = QueueElementAdminForm

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

    search_fields = ('=id',)

    def submission_link(self, obj):
        if obj.submission is None:
            return ''
        url = reverse('admin:ejudge_submission_change',
                      args=[obj.submission.id])
        return '<a href="{}">{}</a>'.format(url, obj.submission)
    submission_link.allow_tags = True


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


class SubmissionAdminForm(django.forms.ModelForm):
    class Meta:
        model = models.Submission
        fields = ('__all__')
        widgets = {
            'result': autocomplete.ModelSelect2(
                url='ejudge:admin:solution-checking-result-autocomplete')
        }


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    form = SubmissionAdminForm

    list_display = (
        'id',
        'ejudge_contest_id',
        'ejudge_submit_id',
        'result_link',
        'updated_at',
    )

    list_filter = ('result__result', 'ejudge_contest_id',)
    search_fields = ('=id', '=ejudge_submit_id',)

    def result_link(self, obj):
        url = reverse('admin:ejudge_solutioncheckingresult_change',
                      args=[obj.result.id])
        return '<a href="{}">{}</a>'.format(url, obj.result)
    result_link.allow_tags = True


admin.site.register(models.TestCheckingResult)
