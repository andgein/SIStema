# -*- coding: utf-8 -*-

from django.db import transaction

import schools.models
import users.models
import modules.study_results.models as study_results_models

from modules.topics import models
from modules.topics import issuer
from modules.topics import mark_guesser

from tools.copy_models import copy_models


class RollbackException(Exception):
    pass


def test_topics():
    try:
        with transaction.atomic():
            _test_topics()
            raise RollbackException()
    except RollbackException:
        pass


def _test_topics():
    Mark = study_results_models.StudyResult.Evaluation
    good_marks = [
        Mark.FOUR_MINUS,
        Mark.FOUR,
        Mark.FOUR_PLUS,
        Mark.FIVE_MINUS,
        Mark.FIVE,
    ]

    print('Making test school...')
    sis2017, school = make_test_school()
    sis2016 = schools.models.School.objects.get(short_name='2016')
    old_questionnaire = models.TopicQuestionnaire.objects.get(school=sis2016)
    questionnaire = models.TopicQuestionnaire.objects.get(school=school)

    print('Testing topics...')
    participants = schools.models.SchoolParticipant.objects.filter(
        school=sis2016,
        study_result__theory__in=good_marks,
        study_result__practice__in=good_marks,
    )

    question_counts = []
    error_counts = []
    for participant in participants:
        user = participant.user

        old_marks = models.UserMark.objects.filter(
            user=user,
            scale_in_topic__topic__questionnaire=old_questionnaire)
        questions_count = ask(questionnaire, user, old_marks)

        new_marks = models.UserMark.objects.filter(
            user=user,
            scale_in_topic__topic__questionnaire=questionnaire)
        errors_count = count_errors(old_marks, new_marks)

        question_counts.append(questions_count)
        error_counts.append(errors_count)
        print('{}: q = {}, e = {}'.format(user.get_full_name(),
                                          questions_count,
                                          errors_count))

    print('Mean questions count:', sum(question_counts) / len(question_counts))
    print('Mean errors count:', sum(error_counts) / len(error_counts))


def ask(questionnaire, user, user_marks):
    mark_by_scale = {_scale_in_topic_key(mark.scale_in_topic): mark.mark
                     for mark in user_marks}
    guesser = mark_guesser.MarkGuesser(user, questionnaire)
    topic_issuer = issuer.TopicIssuer(user, questionnaire)
    question_count = 0
    while True:
        # Issue
        guesser.update_automatically_marks()
        topic_issue = topic_issuer.find_and_issue_new_topic_for_user()
        if topic_issue:
            question_count += 1
        else:
            break
        # Answer
        answered_label_groups = [x.label_group
                                 for x in topic_issue.scales.all()]
        for scale_in_topic in topic_issue.topic.scaleintopic_set.all():
            if scale_in_topic.scale_label_group in answered_label_groups:
                models.UserMark.objects.create(
                    user=user,
                    scale_in_topic=scale_in_topic,
                    mark=mark_by_scale[_scale_in_topic_key(scale_in_topic)],
                )

    return question_count


def _scale_in_topic_key(scale_in_topic):
    return '{}:{}'.format(scale_in_topic.topic.short_name,
                          scale_in_topic.scale_label_group.scale.short_name)


def count_errors(old_marks, new_marks):
    return len(_marks_set(new_marks) - _marks_set(old_marks))

def _marks_set(marks):
    return {
        '{}:{}:{}'.format(
            mark.scale_in_topic.topic.short_name,
            mark.scale_in_topic.scale_label_group.scale.short_name,
            mark.mark)
        for mark in marks}


def make_test_school():
    sis_2017 = schools.models.School.objects.get(short_name='2017')
    sis_test = schools.models.School.objects.create(
        name='SIS test',
        short_name='sis.test')

    copy_models(sis_2017, sis_test, [
        models.Topic,
        models.TopicQuestionnaire,
        models.LevelUpwardDependency,
        models.LevelDownwardDependency,
        models.ScaleLabel,
        models.ScaleInTopic,
        models.TopicDependency,
    ])

    return sis_2017, sis_test
