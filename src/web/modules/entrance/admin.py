from django.contrib import admin

from home.admin import AbstractHomePageBlockAdmin
from . import models

import users.models


class EntranceExamTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'exam', 'order')
    list_filter = ('exam',)
    ordering = ('exam', 'order')


class TestEntranceExamTaskAdmin(EntranceExamTaskAdmin):
    pass

admin.site.register(models.TestEntranceExamTask, TestEntranceExamTaskAdmin)


class FileEntranceExamTaskAdmin(EntranceExamTaskAdmin):
    pass

admin.site.register(models.FileEntranceExamTask, FileEntranceExamTaskAdmin)


class ProgramEntranceExamTaskAdmin(EntranceExamTaskAdmin):
    pass

admin.site.register(models.ProgramEntranceExamTask, ProgramEntranceExamTaskAdmin)

admin.site.register(models.EntranceExam)


class EntranceLevelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'short_name',
        'name',
        'order',
        'school',
    )

admin.site.register(models.EntranceLevel, EntranceLevelAdmin)


class EntranceExamTaskSolutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'user', 'ip')
    list_filter = ('task',)
    search_fields = (
        '=user__username',
        '=user__email',
        '=user__first_name',
        '=user__last_name',
        '=ip',
    )

admin.site.register(models.EntranceExamTaskSolution, EntranceExamTaskSolutionAdmin)


class ProgramEntranceExamTaskSolutionAdmin(EntranceExamTaskSolutionAdmin):
    list_display = EntranceExamTaskSolutionAdmin.list_display + (
        'language',
        'ejudge_queue_element',
    )

    list_filter = EntranceExamTaskSolutionAdmin.list_filter + (
        'language',
    )

admin.site.register(models.ProgramEntranceExamTaskSolution, ProgramEntranceExamTaskSolutionAdmin)


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

admin.site.register(models.EntranceLevelUpgrade, EntranceLevelUpgradeAdmin)


class SolveTaskEntranceLevelUpgradeRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'base_level', 'task')
    list_filter = ('base_level', 'task')

admin.site.register(models.SolveTaskEntranceLevelUpgradeRequirement,
                    SolveTaskEntranceLevelUpgradeRequirementAdmin)


class CheckingGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'short_name', 'name')
    list_filter = ('school', )

admin.site.register(models.CheckingGroup, CheckingGroupAdmin)


class UserInCheckingGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'group', 'is_actual')
    list_filter = ('group', 'is_actual')

admin.site.register(models.UserInCheckingGroup, UserInCheckingGroupAdmin)


class CheckingLockAdmin(admin.ModelAdmin):
    list_display = ('id', 'locked_user', 'locked_by', 'locked_until')
    list_filter = (('locked_by', admin.RelatedOnlyFieldListFilter), )

admin.site.register(models.CheckingLock, CheckingLockAdmin)


class SolutionScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'solution', 'scored_by', 'score', 'created_at')
    list_filter = (('scored_by', admin.RelatedOnlyFieldListFilter), )

admin.site.register(models.SolutionScore, SolutionScoreAdmin)


class CheckingCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'commented_by', 'comment', 'created_at')
    list_filter = ('school', ('commented_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

admin.site.register(models.CheckingComment, CheckingCommentAdmin)


class EntranceRecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'checked_by', 'parallel', 'created_at', 'score')
    list_filter = ('school', ('checked_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

admin.site.register(models.EntranceRecommendation, EntranceRecommendationAdmin)


class EntranceStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'created_by', 'public_comment', 'is_status_visible', 'status', 'session', 'parallel', 'created_at', 'updated_at')
    list_filter = ('school', 'status', 'session', 'parallel', ('created_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'public_comment')

admin.site.register(models.EntranceStatus, EntranceStatusAdmin)


class AbstractAbsenceReasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'created_by', 'public_comment',
                    'private_comment', 'created_at')
    list_filter = ('school', ('created_by', admin.RelatedOnlyFieldListFilter))
    search_fields = ('user__first_name', 'user__last_name', 'user__username',
                     'public_comment')

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

admin.site.register(models.RejectionAbsenceReason,
                    AbstractAbsenceReasonAdmin)
admin.site.register(models.NotConfirmedAbsenceReason,
                    AbstractAbsenceReasonAdmin)


admin.site.register(models.EntranceStepsHomePageBlock,
                    AbstractHomePageBlockAdmin)


class AbstractEntranceStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'order',
                    'available_from_time', 'available_to_time',
                    'available_after_step')
    list_filter = (('school', admin.RelatedOnlyFieldListFilter), )
    ordering = ('school', 'order')

admin.site.register(models.ConfirmProfileEntranceStep,
                    AbstractEntranceStepAdmin)
admin.site.register(models.FillQuestionnaireEntranceStep,
                    AbstractEntranceStepAdmin)
admin.site.register(models.SolveExamEntranceStep,
                    AbstractEntranceStepAdmin)
admin.site.register(models.ResultsEntranceStep,
                    AbstractEntranceStepAdmin)
admin.site.register(models.MakeUserParticipatingEntranceStep,
                    AbstractEntranceStepAdmin)
