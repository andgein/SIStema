from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter)

from modules.entrance import models
import home.models
import sistema.polymorphic

import users.models
import groups.admin


@admin.register(models.EntranceExamTask)
class EntranceExamTaskAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.EntranceExamTask
    list_display = ('id', 'get_class', 'title', 'exam', 'order')
    list_filter = ('exam', PolymorphicChildModelFilter)
    ordering = ('exam', 'order')


@admin.register(models.TestEntranceExamTask)
@admin.register(models.FileEntranceExamTask)
@admin.register(models.ProgramEntranceExamTask)
@admin.register(models.OutputOnlyEntranceExamTask)
class EntranceExamTaskChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceExamTask


@admin.register(models.EntranceExam)
class EntranceExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'close_time')
    list_filter = ('school',)
    search_fields = ('=id',)
    ordering = ('-school', 'id')


@admin.register(models.EntranceLevel)
class EntranceLevelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'short_name',
        'name',
        'order',
        'school',
    )


@admin.register(models.EntranceLevelOverride)
class EntranceLevelOverrideAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'user',
        'entrance_level',
    )

    list_filter = (
        'school',
        'entrance_level',
    )

    search_fields = (
        '=id',
        'user__email',
        'user__profile__first_name',
        'user__profile__middle_name',
        'user__profile__last_name',
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
        'user__profile__first_name',
        'user__profile__last_name',
        '=ip',
    )


@admin.register(models.TestEntranceExamTaskSolution)
@admin.register(models.FileEntranceExamTaskSolution)
@admin.register(models.ProgramEntranceExamTaskSolution)
@admin.register(models.OutputOnlyEntranceExamTaskSolution)
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
        'user__profile__first_name',
        'user__profile__last_name',
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
    list_display = ('id', 'user', 'task', 'locked_by', 'locked_until')
    list_filter = (('locked_by', admin.RelatedOnlyFieldListFilter), )


@admin.register(models.CheckedSolution)
class CheckedSolutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'solution', 'checked_by', 'score', 'comment', 'created_at')
    list_filter = (('checked_by', admin.RelatedOnlyFieldListFilter), )


@admin.register(models.CheckingComment)
class CheckingCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'commented_by', 'comment', 'created_at')
    list_filter = ('school', ('commented_by', admin.RelatedOnlyFieldListFilter))
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username')


@admin.register(models.EntranceStatus)
class EntranceStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'user',
        'created_by',
        'public_comment',
        'private_comment',
        'is_status_visible',
        'status',
        'session',
        'parallel',
        'created_at',
        'updated_at',
    )
    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
        'status',
        'session',
        'parallel',
        ('created_by', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username',
        'public_comment')


@admin.register(models.AbstractAbsenceReason)
class AbstractAbsenceReasonAdmin(
        sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractAbsenceReason
    list_display = (
        'id',
        'get_class',
        'school',
        'user',
        'created_by',
        'public_comment',
        'private_comment',
        'created_at',
    )
    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
        ('created_by', admin.RelatedOnlyFieldListFilter),
        PolymorphicChildModelFilter,
    )
    search_fields = (
        '=id',
        '=user__id',
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username',
        'user__email',
        'public_comment',
        'private_comment',
    )


@admin.register(models.RejectionAbsenceReason)
@admin.register(models.NotConfirmedAbsenceReason)
class AbsenceReasonChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.RejectionAbsenceReason

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = (
                users.models.User.objects.filter(
                    entrance_statuses__status=models.EntranceStatus.Status.ENROLLED
                ).distinct().order_by('profile__last_name', 'profile__first_name'))
        if db_field.name == 'created_by':
            kwargs['queryset'] = (
                users.models.User.objects.filter(
                    is_staff=1
                ).order_by('profile__last_name', 'profile__first_name'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(models.EntranceStepsHomePageBlock)
class EntranceStepsHomePageBlockAdmin(PolymorphicChildModelAdmin):
    base_model = home.models.AbstractHomePageBlock


@admin.register(models.AbstractEntranceStep)
class EntranceStepsAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.AbstractEntranceStep
    list_display = ('id',
                    'get_real_instance_str',
                    'get_class',
                    'school', 'order',
                    'get_available_from_time',
                    'get_available_to_time',
                    'available_after_step')
    list_display_links = ('id', 'get_real_instance_str')
    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
        PolymorphicChildModelFilter
    )
    ordering = ('school', 'order')

    def get_class(self, obj):
        """
        Truncates EntranceStep from class name
        """
        class_name = super().get_class(obj)
        if class_name.endswith('EntranceStep'):
            return class_name[:-len('EntranceStep')]
        return class_name
    get_class.short_description = 'Type'

    def get_available_from_time(self, obj):
        if obj.available_from_time is None:
            return None
        return obj.available_from_time.datetime
    get_available_from_time.short_description = 'Available from'
    get_available_from_time.admin_order_field = 'available_from_time__datetime'

    def get_available_to_time(self, obj):
        if obj.available_to_time is None:
            return None
        return obj.available_to_time.datetime
    get_available_to_time.short_description = 'Available to'
    get_available_to_time.admin_order_field = 'available_to_time__datetime'


@admin.register(models.ConfirmProfileEntranceStep)
@admin.register(models.EnsureProfileIsFullEntranceStep)
@admin.register(models.FillQuestionnaireEntranceStep)
@admin.register(models.SolveExamEntranceStep)
@admin.register(models.ResultsEntranceStep)
@admin.register(models.MakeUserParticipatingEntranceStep)
@admin.register(models.MarkdownEntranceStep)
class EntranceStepChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractEntranceStep


class UserParticipatedInSchoolEntranceStepExceptionInline(admin.StackedInline):
    model = models.UserParticipatedInSchoolEntranceStepException
    extra = 0


@admin.register(models.UserParticipatedInSchoolEntranceStep)
class UserParticipatedInSchoolEntranceStepChildAdmin(
        PolymorphicChildModelAdmin
):
    base_model = models.AbstractEntranceStep
    inlines = (
        UserParticipatedInSchoolEntranceStepExceptionInline,
    )


@admin.register(models.EntranceUserMetric)
class EntranceUserMetricAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.EntranceUserMetric
    list_display = ('id', 'exam', 'name')
    list_filter = ('exam', PolymorphicChildModelFilter)
    ordering = ('-exam', '-id')


class ParallelScoreEntranceUserMetricFileTaskEntryInline(admin.StackedInline):
    model = models.ParallelScoreEntranceUserMetricFileTaskEntry
    extra = 1


class ParallelScoreEntranceUserMetricProgramTaskEntryInline(
        admin.StackedInline
):
    model = models.ParallelScoreEntranceUserMetricProgramTaskEntry
    extra = 1


@admin.register(models.ParallelScoreEntranceUserMetric)
class ParallelScoreEntranceUserMetricAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceUserMetric
    inlines = (
        ParallelScoreEntranceUserMetricFileTaskEntryInline,
        ParallelScoreEntranceUserMetricProgramTaskEntryInline,
    )


@admin.register(models.EntranceStatusGroup)
class EntranceStatusGroupAdmin(groups.admin.AbstractGroupAdmin):
    base_model = models.EntranceStatusGroup
