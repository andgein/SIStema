from django.contrib import admin
import django.forms

from dal import autocomplete

from modules.smartq import models


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'short_name',
        'created_date',
        'modified_date',
    )


class GeneratedQuestionAdminForm(django.forms.ModelForm):
    class Meta:
        model = models.GeneratedQuestion
        fields = ('__all__')
        widgets = {
            'user': autocomplete.ModelSelect2(
                url='users_admin:user-autocomplete')
        }


@admin.register(models.GeneratedQuestion)
@admin.register(models.StaffGeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    form = GeneratedQuestionAdminForm

    list_display = (
        'base_question',
        'seed',
        'user',
    )

    list_filter = (
        'base_question',
    )

    search_fields = (
        'base_question__short_name',
        '=seed',
        'user__profile__first_name',
        'user__profile__middle_name',
        'user__profile__last_name',
    )
