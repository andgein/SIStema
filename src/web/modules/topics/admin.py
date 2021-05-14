from django.contrib import admin

import modules.entrance.admin as entrance_admin
from . import models


@admin.register(models.TopicQuestionnaire)
class TopicQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'school')
    autocomplete_fields = ('previous',)
    search_fields = ('title', 'school__name',)


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'short_name',
        'title',
        'level',
        'order',
        'questionnaire',
        'get_tags',
    )

    list_filter = ('questionnaire', 'level', 'tags')
    autocomplete_fields = ('questionnaire', 'level', 'tags')
    search_fields = ('short_name', 'title', 'questionnaire__school__name')
    ordering = ('order',)

    def get_tags(self, obj):
        return ", ".join(tag.title for tag in obj.tags.order_by('short_name').all())


@admin.register(models.TopicDependency)
class TopicDependencyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source',
        'destination',
        'source_mark',
        'destination_mark',
    )

    autocomplete_fields = ('source', 'destination')

    search_fields = (
        'source__topic__short_name',
        'destination__topic__short_name',
    )

    ordering = (
        'source__topic__short_name',
        'destination__topic__short_name',
        'source_mark',
        'destination_mark',
    )


@admin.register(models.Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'questionnaire')
    autocomplete_fields = ('questionnaire',)
    search_fields = ('name', 'questionnaire__school__name',)


@admin.register(models.LevelDownwardDependency)
@admin.register(models.LevelUpwardDependency)
class LevelDependencyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source_level',
        'destination_level',
        'min_percent',
    )
    autocomplete_fields = ('questionnaire', 'source_level', 'destination_level')


@admin.register(models.Scale)
class ScaleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'short_name',
        'title',
        'count_values',
        'questionnaire',
    )
    autocomplete_fields = ('questionnaire',)
    search_fields = ('short_name', 'title', 'questionnaire__school__name')


@admin.register(models.ScaleLabelGroup)
class ScaleLabelGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'scale')
    list_filter = ('scale__questionnaire', )
    autocomplete_fields = ('scale',)
    search_fields = (
        'short_name',
        'scale__short_name',
        'scale__title',
        'scale__questionnaire__school__name',
    )


@admin.register(models.ScaleLabel)
class ScaleLabelAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'mark', 'label_text')
    list_filter = ('group__scale__questionnaire', )
    autocomplete_fields = ('group',)


@admin.register(models.ScaleInTopic)
class ScaleInTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'scale_label_group')
    list_filter = ('scale_label_group', 'topic__questionnaire')
    autocomplete_fields = ('topic', 'scale_label_group')
    search_fields = (
        'topic__short_name',
        'topic__title',
        'topic__text',
        'topic__questionnaire__school__name',
    )


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'title', 'questionnaire')
    list_filter = ('questionnaire',)
    autocomplete_fields = ('questionnaire',)
    search_fields = ('short_name', 'title', 'questionnaire__school__name')


@admin.register(models.UserQuestionnaireStatus)
class UserQuestionnaireStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'questionnaire', 'status')
    list_filter = ('status', 'questionnaire')
    autocomplete_fields = ('user', 'questionnaire')
    search_fields = (
        '=user__username',
        '=user__email',
        'user__last_name',
        'user__profile__last_name')


@admin.register(models.UserMark)
class BaseMarkAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'scale_in_topic',
        'mark',
        'is_automatically',
    )

    list_filter = ('mark', 'is_automatically')
    autocomplete_fields = ('user', 'scale_in_topic')
    search_fields = (
        '=user_id',
        '=user__profile__first_name',
        '=user__profile__last_name',
        '=user__username',
        '=user__email',
        '=scale_in_topic__topic__short_name',
        '=scale_in_topic__topic__title',
    )


@admin.register(models.TopicIssue)
class TopicIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'topic', 'is_correcting')
    list_filter = ('is_correcting',)
    autocomplete_fields = ('user', 'topic')
    search_fields = (
        'user__username',
        'user__email',
        'user__profile__first_name',
        'user__profile__last_name',
        'user__first_name',
        'user__last_name',
        'topic__short_name',
        'topic__title',
    )


@admin.register(models.ScaleInTopicIssue)
class ScaleInTopicIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic_issue', 'label_group')
    autocomplete_fields = ('topic_issue', 'label_group')


@admin.register(models.EntranceLevelRequirement)
class EntranceLevelRequirementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'entrance_level',
        'tag',
        'max_penalty',
        'questionnaire',
    )
    list_filter = ('questionnaire',)
    autocomplete_fields = ('entrance_level', 'tag', 'questionnaire')
    search_fields = ('entrance_level__short_name', 'entrance_level__name')


@admin.register(models.FillTopicsQuestionnaireEntranceStep)
class FillTopicsQuestionnaireEntranceStepAdmin(
        entrance_admin.EntranceStepChildAdmin):
    autocomplete_fields = (
        entrance_admin.EntranceStepChildAdmin.autocomplete_fields +
        ('questionnaire',))


@admin.register(models.QuestionForTopic)
class QuestionForTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'scale_in_topic', 'smartq_question', 'mark', 'group')
    list_filter = ('scale_in_topic', 'smartq_question')
    autocomplete_fields = ('scale_in_topic', 'smartq_question')
    search_fields = (
        'scale_in_topic__topic__short_name',
        'scale_in_topic__topic__title',
        'smartq_question__short_name',
    )


@admin.register(models.TopicCheckingQuestionnaire)
class TopicCheckingQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'topic_questionnaire', 'status', 'checked_at')
    list_filter = ('topic_questionnaire',)
    autocomplete_fields = ('user', 'topic_questionnaire')
    search_fields = (
        'user__username',
        'user__email',
        'user__profile__first_name',
        'user__profile__last_name',
    )


@admin.register(models.TopicCheckingQuestionnaireQuestion)
class TopicCheckingQuestionnaireQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'questionnaire',
        'generated_question',
        'checker_result',
        'checker_message',
    )
    autocomplete_fields = (
        'questionnaire',
        'generated_question',
        'topic_mapping',
    )
    search_fields = ('=questionnaire__id',)


@admin.register(models.TopicCheckingSettings)
class TopicCheckingSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'questionnaire', 'max_questions')
    autocomplete_fields = ('questionnaire',)


@admin.register(models.TopicsEntranceLevelLimit)
class TopicsEntranceLevelLimitAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'level', 'questionnaire')
    list_filter = ('questionnaire', 'level')
    autocomplete_fields = ('user', 'level', 'questionnaire')
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'questionnaire__school__name',
    )


@admin.register(models.TopicsEntranceLevelLimiter)
class TopicsEntranceLevelLimiterChildAdmin(entrance_admin.EntranceLevelLimiterChildAdmin):
    pass
