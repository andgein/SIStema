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
    )

    search_fields = (
        'base_question__short_name',
        '=seed',
    )

admin.site.register(models.GeneratedQuestion, GeneratedQuestionAdmin)
admin.site.register(models.StaffGeneratedQuestion, GeneratedQuestionAdmin)
