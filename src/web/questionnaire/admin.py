from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter,
                               PolymorphicParentModelAdmin)

import sistema.polymorphic
from . import models


class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'title', 'school', 'session')


admin.site.register(models.Questionnaire, QuestionnaireAdmin)


@admin.register(models.AbstractQuestionnaireBlock)
class AbstractQuestionnaireBlockAdmin(
        sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractQuestionnaireBlock
    list_display = (
        'id',
        'questionnaire',
        'short_name',
        'order',
    )
    list_filter = ('questionnaire', PolymorphicChildModelFilter)
    ordering = ('questionnaire', 'order')


@admin.register(models.AbstractQuestionnaireQuestion)
@admin.register(models.MarkdownQuestionnaireBlock)
@admin.register(models.TextQuestionnaireQuestion)
@admin.register(models.YesNoQuestionnaireQuestion)
@admin.register(models.DateQuestionnaireQuestion)
class AbstractQuestionnaireBlockChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractQuestionnaireBlock


class ChoiceQuestionnaireQuestionVariantInline(admin.TabularInline):
    model = models.ChoiceQuestionnaireQuestionVariant
    extra = 1
    ordering = ('order',)


@admin.register(models.ChoiceQuestionnaireQuestion)
class ChoiceQuestionnaireQuestionQuestionChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractQuestionnaireBlock
    inlines = (ChoiceQuestionnaireQuestionVariantInline,)


class ChoiceQuestionnaireQuestionVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text')
    list_filter = ('question',)


admin.site.register(models.ChoiceQuestionnaireQuestionVariant,
                    ChoiceQuestionnaireQuestionVariantAdmin)


class UserQuestionnaireStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'questionnaire', 'status')
    list_filter = ('questionnaire', 'status')
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
        'user__profile__first_name',
        'user__profile__last_name',
    )


admin.site.register(models.UserQuestionnaireStatus, UserQuestionnaireStatusAdmin)


class QuestionnaireAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'questionnaire', 'question_short_name', 'answer')
    list_filter = ('questionnaire',)
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
        'user__profile__first_name',
        'user__profile__last_name',
    )


admin.site.register(models.QuestionnaireAnswer, QuestionnaireAnswerAdmin)


class QuestionnaireBlockShowConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'block', 'need_to_be_checked')
    list_filter = ('block__questionnaire',)


admin.site.register(models.QuestionnaireBlockShowCondition, QuestionnaireBlockShowConditionAdmin)
