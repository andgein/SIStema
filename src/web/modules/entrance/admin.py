from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter)

import groups.admin
import home.models
import sistema.polymorphic
from modules.entrance import models


@admin.register(models.EntranceExamTask)
class EntranceExamTaskAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.EntranceExamTask
    list_display = ('id', 'get_description_html', 'category', 'order')
    list_display_links = ('id', 'get_description_html')
    list_filter = ('exam', PolymorphicChildModelFilter)
    ordering = ('exam', 'order')
    autocomplete_fields = ('exam', 'category')
    search_fields = ('title', 'exam__school__name')


@admin.register(models.EntranceExamTaskCategory)
class EntranceExamTaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'title', 'order')
    list_filter = ('exam',)
    ordering = ('-exam', 'order')
    autocomplete_fields = ('exam', 'available_from_time', 'available_to_time')
    search_fields = ('=id', 'title', 'exam__school__name')


@admin.register(models.TestEntranceExamTask)
@admin.register(models.FileEntranceExamTask)
@admin.register(models.ProgramEntranceExamTask)
@admin.register(models.OutputOnlyEntranceExamTask)
class EntranceExamTaskChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceExamTask
    autocomplete_fields = EntranceExamTaskAdmin.autocomplete_fields
    search_fields = EntranceExamTaskAdmin.search_fields


@admin.register(models.EntranceExam)
class EntranceExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'close_time')
    list_filter = ('school',)
    search_fields = ('=id', 'school__name')
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
    ordering = ('-school__year', '-school__name', 'name')
    search_fields = ('short_name', 'name', 'school__name')
    autocomplete_fields = ('tasks', )


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

    autocomplete_fields = ('user',)

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
    list_display = ('id', 'get_description_html', 'task', 'user', 'ip')
    list_display_links = ('id', 'get_description_html')
    list_filter = ('task', PolymorphicChildModelFilter)
    autocomplete_fields = ('task', 'user')
    search_fields = (
        '=user__username',
        '=user__email',
        'user__profile__first_name',
        'user__profile__last_name',
        '=ip',
    )

    def get_real_instance_str(self, obj):
        return '{}: «{}»'.format(obj.user.get_full_name(), obj.task)


@admin.register(models.TestEntranceExamTaskSolution)
@admin.register(models.FileEntranceExamTaskSolution)
class EntranceExamTaskSolutionChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceExamTaskSolution
    autocomplete_fields = EntranceExamTaskSolutionAdmin.autocomplete_fields


@admin.register(models.OutputOnlyEntranceExamTaskSolution)
class EjudgeEntranceExamTaskSolutionChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceExamTaskSolution
    autocomplete_fields = EntranceExamTaskSolutionAdmin.autocomplete_fields + (
        'ejudge_queue_element',
    )


@admin.register(models.ProgramEntranceExamTaskSolution)
class ProgramEntranceExamTaskSolutionChildAdmin(
        EjudgeEntranceExamTaskSolutionChildAdmin):
    autocomplete_fields = (
        EjudgeEntranceExamTaskSolutionChildAdmin.autocomplete_fields +
        ('language',))


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
    autocomplete_fields = ('user',)
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
    autocomplete_fields = ('task',)


@admin.register(models.CheckingGroup)
class CheckingGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'short_name', 'name')
    list_filter = ('school', )
    autocomplete_fields = ('tasks', 'group')
    search_fields = ('school__name', 'name')


@admin.register(models.CheckingLock)
class CheckingLockAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'task', 'locked_by', 'locked_until')
    list_filter = (('locked_by', admin.RelatedOnlyFieldListFilter), )
    autocomplete_fields = ('user', 'task', 'locked_by')


@admin.register(models.CheckedSolution)
class CheckedSolutionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'solution',
        'checked_by',
        'score',
        'comment',
        'created_at',
    )
    list_filter = (('checked_by', admin.RelatedOnlyFieldListFilter), )
    autocomplete_fields = ('solution', 'checked_by')


@admin.register(models.CheckingComment)
class CheckingCommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'school',
        'user',
        'commented_by',
        'comment',
        'created_at',
    )
    list_filter = ('school', ('commented_by', admin.RelatedOnlyFieldListFilter))
    autocomplete_fields = ('user', 'commented_by')
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username')


class EnrolledSessionAndParallelAdmin(admin.TabularInline):
    model = models.EnrolledToSessionAndParallel
    extra = 1
    autocomplete_fields = ('session', 'parallel')


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
        'get_sessions',
        'get_parallels',
        'created_at',
        'updated_at',
        'is_approved',
    )
    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
        'status',
        'sessions_and_parallels__session',
        'sessions_and_parallels__parallel',
        ('created_by', admin.RelatedOnlyFieldListFilter),
        'is_approved',
    )
    autocomplete_fields = ('user', 'created_by')
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username',
        'public_comment'
    )
    inlines = (EnrolledSessionAndParallelAdmin, )

    def get_sessions(self, obj):
        return ', '.join(set(
            obj.sessions_and_parallels
               .filter(session__isnull=False)
               .values_list('session__name', flat=True)
        ))

    get_sessions.short_description = 'Session'

    def get_parallels(self, obj):
        return ', '.join(set(
            obj.sessions_and_parallels
               .filter(parallel__isnull=False)
               .values_list('parallel__name', flat=True)
        ))

    get_parallels.short_description = 'Parallel'


@admin.register(models.AbstractAbsenceReason)
class AbstractAbsenceReasonAdmin(
        sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractAbsenceReason
    list_display = (
        'id',
        'get_description_html',
        'school',
        'user',
        'created_by',
        'public_comment',
        'private_comment',
        'created_at',
    )
    list_display_links = ('id', 'get_description_html')
    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
        ('created_by', admin.RelatedOnlyFieldListFilter),
        PolymorphicChildModelFilter,
    )
    autocomplete_fields = ('user', 'created_by')
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
    autocomplete_fields = AbstractAbsenceReasonAdmin.autocomplete_fields
    search_fields = AbstractAbsenceReasonAdmin.search_fields


@admin.register(models.EntranceStepsHomePageBlock)
class EntranceStepsHomePageBlockAdmin(PolymorphicChildModelAdmin):
    base_model = home.models.AbstractHomePageBlock


@admin.register(models.AbstractEntranceStep)
class EntranceStepsAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.AbstractEntranceStep
    list_display = (
        'id',
        'get_description_html',
        'school', 'order',
        'get_available_from_time',
        'get_available_to_time',
        'available_after_step',
    )
    list_display_links = ('id', 'get_description_html')
    list_filter = (
        ('school', admin.RelatedOnlyFieldListFilter),
        PolymorphicChildModelFilter
    )
    ordering = ('school', 'order')
    autocomplete_fields = (
        'session',
        'parallel',
        'available_from_time',
        'available_to_time',
    )
    search_fields = ('=id', 'school__name')

    def get_class(self, obj):
        """
        Truncates EntranceStep from class name
        """
        class_name = super().get_class(obj)
        if class_name.endswith('EntranceStep'):
            return class_name[:-len('EntranceStep')]
        return class_name

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
@admin.register(models.SolveExamEntranceStep)
@admin.register(models.ResultsEntranceStep)
@admin.register(models.MakeUserParticipatingEntranceStep)
@admin.register(models.MarkdownEntranceStep)
@admin.register(models.UserIsMemberOfGroupEntranceStep)
class EntranceStepChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractEntranceStep
    autocomplete_fields = EntranceStepsAdmin.autocomplete_fields
    search_fields = EntranceStepsAdmin.search_fields


@admin.register(models.FillQuestionnaireEntranceStep)
class FillQuestionnaireEntranceStepChildAdmin(EntranceStepChildAdmin):
    autocomplete_fields = EntranceStepChildAdmin.autocomplete_fields + (
        'questionnaire',
    )


@admin.register(models.EnrollmentType)
class EnrollmentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'step', 'needs_moderation')
    list_display_links = ('id', 'text')
    list_filter = ('step__school', 'needs_moderation')
    search_fields = ('=id', 'text')
    ordering = ('step__school', 'step', 'text')


class EnrollmentTypeInline(admin.TabularInline):
    model = models.EnrollmentType
    extra = 0


@admin.register(models.SelectEnrollmentTypeEntranceStep)
class SelectEnrollmentTypeEntranceStepChildAdmin(EntranceStepChildAdmin):
    inlines = (EnrollmentTypeInline, )


class UserParticipatedInSchoolEntranceStepExceptionInline(admin.StackedInline):
    model = models.UserParticipatedInSchoolEntranceStepException
    extra = 0
    autocomplete_fields = ('user',)


@admin.register(models.UserParticipatedInSchoolEntranceStep)
class UserParticipatedInSchoolEntranceStepChildAdmin(EntranceStepChildAdmin):
    inlines = (UserParticipatedInSchoolEntranceStepExceptionInline,)


@admin.register(models.SelectedEnrollmentType)
class SelectedEnrollmentTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'get_review_page_link',
        'is_moderated',
        'is_approved',
        'parallel',
        'entrance_level',
        'reviewed_by',
        'enrollment_type',
    )
    list_display_links = ('id', 'user')
    list_filter = ('enrollment_type__step__school', 'is_moderated', 'is_approved')
    autocomplete_fields = (
        'user',
        'step',
        'enrollment_type',
        'parallel',
        'entrance_level',
        'reviewed_by',
    )

    def get_review_page_link(self, obj):
        return mark_safe(
            '<a href="{}" target="_blank">Информация</a>'
            .format(reverse(
                'school:entrance:enrollment_type_review_user',
                kwargs={
                    'school_name': obj.step.school.short_name,
                    'user_id': obj.user_id,
                }))
        )

    get_review_page_link.short_description = 'информация'


@admin.register(models.EntranceUserMetric)
class EntranceUserMetricAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.EntranceUserMetric
    list_display = ('id', 'exam', 'name')
    list_filter = ('exam', PolymorphicChildModelFilter)
    ordering = ('-exam', '-id')


class ParallelScoreEntranceUserMetricFileTaskEntryInline(admin.StackedInline):
    model = models.ParallelScoreEntranceUserMetricFileTaskEntry
    extra = 1
    autocomplete_fields = ('task',)


class ParallelScoreEntranceUserMetricProgramTaskEntryInline(
        admin.StackedInline):
    model = models.ParallelScoreEntranceUserMetricProgramTaskEntry
    extra = 1
    autocomplete_fields = ('task',)


@admin.register(models.ParallelScoreEntranceUserMetric)
class ParallelScoreEntranceUserMetricAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceUserMetric
    inlines = (
        ParallelScoreEntranceUserMetricFileTaskEntryInline,
        ParallelScoreEntranceUserMetricProgramTaskEntryInline,
    )


@admin.register(models.EntranceStatusGroup)
class EntranceStatusGroupAdmin(groups.admin.AbstractGroupChildAdmin):
    base_model = models.EntranceStatusGroup


@admin.register(models.EnrollmentApprovingStatusGroup)
class EnrollmentApprovingStatusGroupAdmin(groups.admin.AbstractGroupChildAdmin):
    base_model = models.EnrollmentApprovingStatusGroup


@admin.register(models.EnrolledUsersGroup)
class EnrolledUsersGroupAdmin(groups.admin.AbstractGroupChildAdmin):
    base_model = models.EnrolledUsersGroup
    autocomplete_fields = (
        groups.admin.AbstractGroupChildAdmin.autocomplete_fields +
        ('session', 'parallel')
    )


@admin.register(models.SelectedEnrollmentTypeGroup)
class SelectedEnrollmentTypeGroupAdmin(groups.admin.AbstractGroupChildAdmin):
    base_model = models.SelectedEnrollmentTypeGroup
    autocomplete_fields = (
        groups.admin.AbstractGroupChildAdmin.autocomplete_fields +
        ('enrollment_type', )
    )


@admin.register(models.UsersParticipatedInSchoolGroup)
class SchoolGroupAdmin(groups.admin.AbstractGroupChildAdmin):
    base_model = models.UsersParticipatedInSchoolGroup


@admin.register(models.EntranceLevelLimiter)
class EntranceLevelLimiterAdmin(sistema.polymorphic.PolymorphicParentModelAdmin):
    base_model = models.EntranceLevelLimiter
    list_display = ('id', 'get_description_html', 'school')
    list_display_links = ('id', 'get_description_html')
    list_filter = ('school', PolymorphicChildModelFilter)
    ordering = ('-school', )
    autocomplete_fields = ('school', )
    search_fields = ('school__name', )


@admin.register(models.EnrollmentTypeEntranceLevelLimiter)
class EntranceLevelLimiterChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.EntranceLevelLimiter
    autocomplete_fields = EntranceLevelLimiterAdmin.autocomplete_fields
    search_fields = EntranceLevelLimiterAdmin.search_fields


class AgeEntranceLevelLimiterForClassAdmin(admin.TabularInline):
    model = models.AgeEntranceLevelLimiterForClass
    extra = 1
    autocomplete_fields = ('level', )


@admin.register(models.AgeEntranceLevelLimiter)
class AgeEntranceLevelLimiterAdmin(EntranceLevelLimiterChildAdmin):
    inlines = (AgeEntranceLevelLimiterForClassAdmin, )


class AlreadyWasEntranceLevelLimiterForParallelAdmin(admin.TabularInline):
    model = models.AlreadyWasEntranceLevelLimiterForParallel
    extra = 1
    autocomplete_fields = ('previous_parallel', 'level')


@admin.register(models.AlreadyWasEntranceLevelLimiter)
class AlreadyWasEntranceLevelLimiterAdmin(EntranceLevelLimiterChildAdmin):
    inlines = (AlreadyWasEntranceLevelLimiterForParallelAdmin, )
