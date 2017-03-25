from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter,
                               PolymorphicParentModelAdmin)

import sistema.polymorphic
from home.admin import AbstractHomePageBlockAdmin
from . import models

import users.models


@admin.register(models.EntranceExamTask)
class EntranceExamTaskAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.EntranceExamTask
    list_display = ('id', 'get_class', 'title', 'exam', 'order')
    list_filter = ('exam', PolymorphicChildModelFilter)
    ordering = ('exam', 'order')


@admin.register(models.TestEntranceExamTask)
@admin.register(models.ProgramEntranceExamTask)
@admin.register(models.FileEntranceExamTask)
class EntranceExamTaskChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceExamTask

admin.site.register(models.EntranceExam)


@admin.register(models.EntranceLevel)
class EntranceLevelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'short_name',
        'name',
        'order',
        'school',
    )


@admin.register(models.EntranceExamTaskSolution)
class EntranceExamTaskSolutionAdmin(
    sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.EntranceExamTaskSolution
    list_display = ('id', 'get_class', 'task', 'user', 'ip')
    list_filter = ('task', PolymorphicChildModelFilter)
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
        '=ip',
    )


@admin.register(models.TestEntranceExamTaskSolution)
@admin.register(models.ProgramEntranceExamTaskSolution)
@admin.register(models.FileEntranceExamTaskSolution)
class EntranceExamTaskSolutionChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceExamTaskSolution


@admin.register(models.EntranceLevelUpgrade)
class EntranceLevelUpgradeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_school',
        'upgraded_to',
        'created_at'
    )

    list_filter = ('upgraded_to',)
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
    )

    def get_school(self, obj):
        return obj.upgraded_to.school


@admin.register(models.EntranceLevelUpgradeRequirement)
class EntranceLevelUpgradeRequirementAdmin(
    sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.EntranceLevelUpgradeRequirement
    list_display = ('id', 'get_class', 'base_level')
    list_filter = ('base_level', PolymorphicChildModelFilter)


@admin.register(models.SolveTaskEntranceLevelUpgradeRequirement)
class EntranceLevelUpgradeRequirementChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceLevelUpgradeRequirement


@admin.register(models.CheckingGroup)
class CheckingGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'short_name', 'name')
    list_filter = ('school', )


@admin.register(models.UserInCheckingGroup)
class UserInCheckingGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'group', 'is_actual')
    list_filter = ('group', 'is_actual')


@admin.register(models.CheckingLock)
class CheckingLockAdmin(admin.ModelAdmin):
    list_display = ('id', 'locked_user', 'locked_by', 'locked_until')
    list_filter = (('locked_by', admin.RelatedOnlyFieldListFilter), )


@admin.register(models.SolutionScore)
class SolutionScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'solution', 'scored_by', 'score', 'created_at')
    list_filter = (('scored_by', admin.RelatedOnlyFieldListFilter), )


@admin.register(models.CheckingComment)
class CheckingCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'commented_by', 'comment', 'created_at')
    list_filter = ('school', ('commented_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


@admin.register(models.EntranceRecommendation)
class EntranceRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'checked_by', 'parallel', 'created_at', 'score')
    list_filter = ('school', ('checked_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


@admin.register(models.EntranceStatus)
class EntranceStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'created_by', 'public_comment', 'is_status_visible', 'status', 'session', 'parallel', 'created_at', 'updated_at')
    list_filter = (('school', admin.RelatedOnlyFieldListFilter), 'status', 'session', 'parallel', ('created_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'public_comment')


@admin.register(models.AbstractAbsenceReason)
class AbstractAbsenceReasonAdmin(
    sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractAbsenceReason
    list_display = ('id', 'get_class', 'school', 'user', 'created_by', 'public_comment',
                    'private_comment', 'created_at')
    list_filter = (('school', admin.RelatedOnlyFieldListFilter),
                   ('created_by', admin.RelatedOnlyFieldListFilter),
                   PolymorphicChildModelFilter)
    search_fields = ('user__first_name',
                     'user__last_name',
                     'user__username',
                     'public_comment')


@admin.register(models.RejectionAbsenceReason)
@admin.register(models.NotConfirmedAbsenceReason)
class AbsenceReasonChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.RejectionAbsenceReason

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = (
                users.models.User.objects.filter(
                    entrance_statuses__status=models.EntranceStatus.Status.ENROLLED
                ).distinct().order_by('last_name', 'first_name'))
        if db_field.name == 'created_by':
            kwargs['queryset'] = (
                users.models.User.objects.filter(
                    is_staff=1
                ).order_by('last_name', 'first_name'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(models.EntranceStepsHomePageBlock,
                    AbstractHomePageBlockAdmin)


class AbstractEntranceStepAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractEntranceStep

    list_display = ('id', 'school', 'order',
                    'available_from_time', 'available_to_time',
                    'available_after_step')
    list_filter = (('school', admin.RelatedOnlyFieldListFilter), )
    ordering = ('school', 'order')


@admin.register(models.AbstractEntranceStep)
class EntranceStepsAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.AbstractEntranceStep
    list_display = ('id',
                    'get_class',
                    'school', 'order',
                    'available_from_time',
                    'available_to_time',
                    'available_after_step')
    list_filter = (('school', admin.RelatedOnlyFieldListFilter),
                   )
    ordering = ('school', 'order')


@admin.register(models.ConfirmProfileEntranceStep)
class ConfirmProfileEntranceStepAdmin(AbstractEntranceStepAdmin):
    base_model = models.ConfirmProfileEntranceStep


@admin.register(models.FillQuestionnaireEntranceStep)
class FillQuestionnaireEntranceStepAdmin(AbstractEntranceStepAdmin):
    base_model = models.FillQuestionnaireEntranceStep


@admin.register(models.SolveExamEntranceStep)
class SolveExamEntranceStepAdmin(AbstractEntranceStepAdmin):
    base_model = models.SolveExamEntranceStep


@admin.register(models.ResultsEntranceStep)
class ResultsEntranceStepAdmin(AbstractEntranceStepAdmin):
    base_model = models.ResultsEntranceStep


@admin.register(models.MakeUserParticipatingEntranceStep)
class MakeUserParticipatingEntranceStepAdmin(AbstractEntranceStepAdmin):
    base_model = models.MakeUserParticipatingEntranceStep
