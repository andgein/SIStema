from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter)

import sistema.polymorphic
from . import models

import groups.admin


@admin.register(models.Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'title', 'school', 'session')
    ordering = ('-school__year', '-school__name', 'title')
    autocomplete_fields = ('close_time', 'must_fill')
    search_fields = ('=id', 'school__name', 'short_name', 'title')

    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(models.AbstractQuestionnaireBlock)
class AbstractQuestionnaireBlockAdmin(
        sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractQuestionnaireBlock
    list_display = (
        'id',
        'questionnaire',
        'short_name',
        'get_text',
        'order',
        'is_top_level'
    )
    list_filter = ('questionnaire', PolymorphicChildModelFilter)
    ordering = ('questionnaire', 'is_top_level', 'order')
    autocomplete_fields = ('questionnaire', )
    search_fields = (
        'short_name',
        'questionnaire__title',
        'questionnaire__school__name',
    )

    def get_text(self, obj):
        obj = obj.get_real_instance()
        if hasattr(obj, 'text'):
            return obj.text
        return None

    get_text.short_description = 'Text'


class QuestionnaireBlockVariantCheckedShowConditionInline(admin.StackedInline):
    model = models.QuestionnaireBlockVariantCheckedShowCondition
    extra = 1
    autocomplete_fields = ('need_to_be_checked',)


class QuestionnaireBlockGroupMemberShowConditionInline(admin.StackedInline):
    model = models.QuestionnaireBlockGroupMemberShowCondition
    extra = 1
    autocomplete_fields = ('need_to_be_member',)


@admin.register(models.AbstractQuestionnaireQuestion)
class AbstractQuestionnaireQuestionAdmin(
    sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractQuestionnaireQuestion
    autocomplete_fields = AbstractQuestionnaireBlockAdmin.autocomplete_fields
    search_fields = AbstractQuestionnaireBlockAdmin.search_fields


@admin.register(models.MarkdownQuestionnaireBlock)
@admin.register(models.TextQuestionnaireQuestion)
@admin.register(models.YesNoQuestionnaireQuestion)
@admin.register(models.DateQuestionnaireQuestion)
@admin.register(models.UserListQuestionnaireQuestion)
class AbstractQuestionnaireBlockChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractQuestionnaireBlock
    inlines = (
        QuestionnaireBlockVariantCheckedShowConditionInline,
        QuestionnaireBlockGroupMemberShowConditionInline,
    )
    autocomplete_fields = AbstractQuestionnaireBlockAdmin.autocomplete_fields
    search_fields = AbstractQuestionnaireBlockAdmin.search_fields


class InlineQuestionnaireBlockChildInline(admin.TabularInline):
    model = models.InlineQuestionnaireBlockChild
    extra = 1
    ordering = ('block__order', )
    autocomplete_fields = ('block', )


@admin.register(models.InlineQuestionnaireBlock)
class InlineQuestionnaireBlockChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractQuestionnaireBlock
    inlines = AbstractQuestionnaireBlockChildAdmin.inlines + (
        InlineQuestionnaireBlockChildInline,
    )


class ChoiceQuestionnaireQuestionVariantInline(admin.TabularInline):
    model = models.ChoiceQuestionnaireQuestionVariant
    extra = 1
    ordering = ('order',)


@admin.register(models.ChoiceQuestionnaireQuestion)
class ChoiceQuestionnaireQuestionQuestionChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractQuestionnaireBlock
    inlines = AbstractQuestionnaireBlockChildAdmin.inlines + (
        ChoiceQuestionnaireQuestionVariantInline,
)


@admin.register(models.ChoiceQuestionnaireQuestionVariant)
class ChoiceQuestionnaireQuestionVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'text')
    list_filter = ('question',)
    search_fields = ('text', 'question__text', 'question__questionnaire__title')


@admin.register(models.UserQuestionnaireStatus)
class UserQuestionnaireStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'questionnaire', 'status')
    list_filter = ('questionnaire', 'status')
    autocomplete_fields = ('user', 'questionnaire')
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
        'user__profile__first_name',
        'user__profile__last_name',
    )


@admin.register(models.QuestionnaireAnswer)
class QuestionnaireAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'questionnaire',
        'question_short_name',
        'answer',
    )
    list_filter = ('questionnaire',)
    autocomplete_fields = ('questionnaire', 'user')
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
        'user__profile__first_name',
        'user__profile__last_name',
    )


@admin.register(models.UsersFilledQuestionnaireGroup)
@admin.register(models.UsersNotFilledQuestionnaireGroup)
class QuestionnaireGroupAdmin(groups.admin.AbstractGroupAdmin):
    pass
