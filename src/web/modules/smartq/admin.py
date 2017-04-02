from django.contrib import admin

from modules.smartq import models

class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'short_name',
        'created_date',
        'modified_date',
    )

admin.site.register(models.Question, QuestionAdmin)

class GeneratedQuestionAdmin(admin.ModelAdmin):
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

admin.site.register(models.GeneratedQuestion, GeneratedQuestionAdmin)
admin.site.register(models.StaffGeneratedQuestion, GeneratedQuestionAdmin)
