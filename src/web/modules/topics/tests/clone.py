"""Tests for topics.TopicQuestionnaire cloning"""

import django.test

from schools.models import School
from modules.topics import models


class QuestionnaireCloneTestCase(django.test.TestCase):
    fixtures = [
        'schools-test-sample-schools',
        'smartq-test-sample-questions',
        'topics-test-sample-questionnaire',
    ]

    def setUp(self):
        self.school_1 = School.objects.get(pk=1)
        self.school_2 = School.objects.get(pk=2)

    def test_clone_generic_case(self):
        tq = models.TopicQuestionnaire.objects.get(pk=1)
        new_tq = tq.clone(school=self.school_2)

        # Levels are copied correctly
        self.assertCountEqual(
            new_tq.levels.values_list('name'),
            tq.levels.values_list('name'),
        )

        # Level dependencies are copied correctly
        level_dep_compare_fields = [
            'source_level__name', 'destination_level__name', 'min_percent']
        self.assertCountEqual(
            (models.LevelUpwardDependency.objects
                .filter(questionnaire=new_tq)
                .values_list(*level_dep_compare_fields)),
            (models.LevelUpwardDependency.objects
                .filter(questionnaire=tq)
                .values_list(*level_dep_compare_fields)),
        )
        self.assertCountEqual(
            (models.LevelDownwardDependency.objects
                .filter(questionnaire=new_tq)
                .values_list(*level_dep_compare_fields)),
            (models.LevelDownwardDependency.objects
                .filter(questionnaire=tq)
                .values_list(*level_dep_compare_fields)),
        )

        # Tags are copied correctly
        tag_compare_fields = ['short_name', 'title']
        self.assertCountEqual(
            new_tq.tags.values_list(*tag_compare_fields),
            tq.tags.values_list(*tag_compare_fields),
        )

        # Topics are copied correctly
        topic_compare_fields = [
            'short_name', 'title', 'text', 'level__name', 'order']
        self.assertCountEqual(
            new_tq.topics.values_list(*topic_compare_fields),
            tq.topics.values_list(*topic_compare_fields),
        )

        # Scales are copied correctly
        scale_compare_fields = ['short_name', 'title', 'count_values']
        self.assertCountEqual(
            new_tq.scales.values_list(*scale_compare_fields),
            tq.scales.values_list(*scale_compare_fields),
        )

        # Scale label groups are copied correctly
        label_group_compare_fields = ['scale__short_name', 'short_name']
        self.assertCountEqual(
            (models.ScaleLabelGroup.objects
                .filter(scale__questionnaire=new_tq)
                .values_list(*label_group_compare_fields)),
            (models.ScaleLabelGroup.objects
                .filter(scale__questionnaire=tq)
                .values_list(*label_group_compare_fields)),
        )

        # Scale labels are copied correctly
        scale_label_compare_fields = [
            'mark',
            'label_text',
            'group__short_name',
            'group__scale__short_name',
        ]
        self.assertCountEqual(
            (models.ScaleLabel.objects
                .filter(group__scale__questionnaire=new_tq)
                .values_list(*scale_label_compare_fields)),
            (models.ScaleLabel.objects
                .filter(group__scale__questionnaire=tq)
                .values_list(*scale_label_compare_fields)),
        )

        # ScaleInTopic objects are copied correctly
        scale_in_topic_compare_fields = [
            'topic__short_name', 'scale_label_group__short_name']
        self.assertCountEqual(
            (models.ScaleInTopic.objects
                .filter(topic__questionnaire=new_tq)
                .values_list(*scale_in_topic_compare_fields)),
            (models.ScaleInTopic.objects
                .filter(topic__questionnaire=tq)
                .values_list(*scale_in_topic_compare_fields)),
        )

        # Topic dependencies are copied correctly
        topic_dep_compare_fields = [
            'source__topic__short_name',
            'source__scale_label_group__short_name',
            'source_mark',
            'destination__topic__short_name',
            'destination__scale_label_group__short_name',
            'destination_mark',
        ]
        self.assertCountEqual(
            (models.TopicDependency.objects
                .filter(source__topic__questionnaire=new_tq)
                .values_list(*topic_dep_compare_fields)),
            (models.TopicDependency.objects
                .filter(source__topic__questionnaire=tq)
                .values_list(*topic_dep_compare_fields)),
        )

        # QuestionForTopic objects are copied correctly
        question_for_topic_compare_fields = [
            'scale_in_topic__topic__short_name',
            'scale_in_topic__scale_label_group__short_name',
            'mark',
            'smartq_question_id',
            'group',
        ]
        self.assertCountEqual(
            (models.QuestionForTopic.objects
                .filter(scale_in_topic__topic__questionnaire=new_tq)
                .values_list(*question_for_topic_compare_fields)),
            (models.QuestionForTopic.objects
                .filter(scale_in_topic__topic__questionnaire=tq)
                .values_list(*question_for_topic_compare_fields)),
        )

        # TopicCheckingSettings objects are copied correctly
        settings_compare_fields = ['max_questions']
        self.assertCountEqual(
            (models.TopicCheckingSettings.objects
                .filter(questionnaire=new_tq)
                .values_list(*settings_compare_fields)),
            (models.TopicCheckingSettings.objects
                .filter(questionnaire=tq)
                .values_list(*settings_compare_fields)),
        )
