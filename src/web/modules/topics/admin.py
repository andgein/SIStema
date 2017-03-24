from django.contrib import admin

from . import models
from .entrance import levels
import modules.entrance.admin as entrance_admin


class TopicQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'school')

admin.site.register(models.TopicQuestionnaire, TopicQuestionnaireAdmin)


class TopicAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'short_name',
        'title',
        'level',
        'order',
        'questionnaire',
    )

    list_filter = ('level', 'questionnaire')
    search_fields = ('=short_name', '=title')
    ordering = ('order',)

admin.site.register(models.Topic, TopicAdmin)


class TopicDependencyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source',
        'destination',
        'source_mark',
        'destination_mark',
    )

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

admin.site.register(models.TopicDependency, TopicDependencyAdmin)


class LevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'questionnaire')

admin.site.register(models.Level, LevelAdmin)


class LevelDependencyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source_level',
        'destination_level',
        'min_percent',
    )

admin.site.register(models.LevelDownwardDependency, LevelDependencyAdmin)
admin.site.register(models.LevelUpwardDependency, LevelDependencyAdmin)


class ScaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'title', 'count_values', 'questionnaire')

admin.site.register(models.Scale, ScaleAdmin)


class ScaleLabelGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'scale')

admin.site.register(models.ScaleLabelGroup, ScaleLabelGroupAdmin)


class ScaleLabelAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'mark', 'label_text')

admin.site.register(models.ScaleLabel, ScaleLabelAdmin)


class ScaleInTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'scale_label_group')
    list_filter = ('scale_label_group',)
    search_fields = ('=topic__short_name','=topic__title', '=topic__text')

admin.site.register(models.ScaleInTopic, ScaleInTopicAdmin)


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'title', 'questionnaire')
    list_filter = ('questionnaire',)

admin.site.register(models.Tag, TagAdmin)


class UserQuestionnaireStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'questionnaire', 'status')
    list_filter = ('status', 'questionnaire')
    search_fields = ('=user__username', '=user__email', 'user__last_name')

admin.site.register(models.UserQuestionnaireStatus, UserQuestionnaireStatusAdmin)


class BaseMarkAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'scale_in_topic',
        'mark',
        'is_automatically',
    )

    list_filter = ('mark', 'is_automatically')
    search_fields = (
        '=user__username',
        '=user__email',
        '=scale_in_topic__topic__short_name',
        '=scale_in_topic__topic__title',
    )

admin.site.register(models.UserMark, BaseMarkAdmin)


class TopicIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'topic', 'is_correcting')
    list_filter = ('is_correcting',)
    search_fields = ('=user__username', '=user__email', '=topic__short_name', '=topic__title')

admin.site.register(models.TopicIssue, TopicIssueAdmin)


class ScaleInTopicIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic_issue', 'label_group')

admin.site.register(models.ScaleInTopicIssue, ScaleInTopicIssueAdmin)


class EntranceLevelRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'entrance_level', 'tag', 'max_penalty', 'questionnaire')
    list_filter = ('questionnaire',)
    search_fields = ('=entrance_level__short_name', '=entrance_level__name')

admin.site.register(levels.EntranceLevelRequirement, EntranceLevelRequirementAdmin)


admin.site.register(models.FillTopicsQuestionnaireEntranceStep,
                    entrance_admin.AbstractEntranceStepAdmin)


class QuestionForTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'scale_in_topic', 'smartq_question', 'mark', 'group')
    list_filter = ('scale_in_topic', 'smartq_question')
    search_fields = ('topic__short_name', 'question__short_name')

admin.site.register(models.QuestionForTopic, QuestionForTopicAdmin)


class TopicCheckingQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'topic_questionnaire', 'status', 'checked_at')
    list_filter = ('topic_questionnaire',)
    search_fields = ('user__first_name', 'user__last_name')

admin.site.register(models.TopicCheckingQuestionnaire, TopicCheckingQuestionnaireAdmin)


class TopicCheckingQuestionnaireQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'questionnaire', 'generated_question', 'checker_result', 'checker_message')
    search_fields = ('=questionnaire__id',)

admin.site.register(models.TopicCheckingQuestionnaireQuestion, TopicCheckingQuestionnaireQuestionAdmin)


class TopicCheckingSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'questionnaire', 'max_questions')

admin.site.register(models.TopicCheckingSettings, TopicCheckingSettingsAdmin)
