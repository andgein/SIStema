import collections
import itertools

from django.db.models import Count

from . import models


class MarkGuesser:
    def __init__(self, user, questionnaire):
        self.user = user
        self.questionnaire = questionnaire

    def update_automatically_marks(self):
        self.update_by_topic_dependencies()
        self.update_by_level_dependencies()

    def update_from_previous_questionnaire(self):
        previous_questionnaire = self.questionnaire.previous
        if previous_questionnaire is None:
            return

        possible_marks = self._get_possible_marks()
        for scale_in_topic_id, scale_possible_marks in possible_marks.items():
            if len(scale_possible_marks) == 1:
                models.UserMark.objects.get_or_create(
                    user=self.user,
                    scale_in_topic_id=scale_in_topic_id,
                    defaults={
                        'mark': scale_possible_marks.pop(),
                        'is_automatically': True,
                    })

        self.update_automatically_marks()

    def update_by_topic_dependencies(self):
        user_marks = models.UserMark.objects.filter(
            user=self.user,
            scale_in_topic__topic__questionnaire=self.questionnaire)

        possible_marks = self._get_possible_marks()
        for user_mark in user_marks:
            possible_marks[user_mark.scale_in_topic_id] = {user_mark.mark}

        scales_for_recalculation = collections.deque(possible_marks.keys())

        # Cache all topic dependencies for quick access
        all_topic_dependencies = list(
            models.TopicDependency.objects
            .filter(source__topic__questionnaire=self.questionnaire))
        topic_dependencies_by_source = collections.defaultdict(list)
        for topic_dependency in all_topic_dependencies:
            topic_dependencies_by_source[(topic_dependency.source_id, topic_dependency.source_mark)].append(
                    topic_dependency)

        # While scales_for_recalculations is not empty, pop one of them and try
        # to update likely marks
        while scales_for_recalculation:
            scale_in_topic_id = scales_for_recalculation.popleft()

            new_possible_marks = collections.defaultdict(set)
            for dependency in itertools.chain(*[topic_dependencies_by_source[(scale_in_topic_id, mark)] for mark in
                                                possible_marks[scale_in_topic_id]]):
                new_possible_marks[dependency.destination_id].add(dependency.destination_mark)

            for scale_in_topic_id, scale_possible_marks in new_possible_marks.items():
                old_value = possible_marks[scale_in_topic_id]
                new_value = old_value & scale_possible_marks
                # Success: now we know more
                if old_value != new_value:
                    print('Update ScaleInTopic #%s' % scale_in_topic_id)
                    print('Was %s, new value is %s' % (old_value, new_value))
                    possible_marks[scale_in_topic_id] &= scale_possible_marks
                    if scale_in_topic_id not in scales_for_recalculation:
                        print('Add #%s for recalculation' % scale_in_topic_id)
                        scales_for_recalculation.append(scale_in_topic_id)

        for scale_in_topic_id, scale_possible_marks in possible_marks.items():
            if len(scale_possible_marks) == 1:
                models.UserMark.objects.get_or_create(
                    user=self.user,
                    scale_in_topic_id=scale_in_topic_id,
                    defaults={
                        'mark': scale_possible_marks.pop(),
                        'is_automatically': True,
                    })

    def _get_possible_marks(self):
        scale_in_topics = models.ScaleInTopic.objects.filter(
            topic__questionnaire=self.questionnaire
        ).select_related('scale_label_group__scale')

        possible_marks = {
            self._scale_in_topic_key(scale_in_topic):
                set(range(scale_in_topic.scale.count_values))
            for scale_in_topic in scale_in_topics
        }

        # Consider previous questionnaire, if it exists
        previous_questionnaire = self.questionnaire.previous
        if previous_questionnaire is not None:
            previous_scale_in_topics = models.ScaleInTopic.objects.filter(
                topic__questionnaire=previous_questionnaire
            ).select_related('scale_label_group__scale')

            previous_marks = models.UserMark.objects.filter(
                user=self.user,
                scale_in_topic__topic__questionnaire=previous_questionnaire)

            for user_mark in previous_marks:
                key = self._scale_in_topic_key(user_mark.scale_in_topic)
                if key in possible_marks:
                    for m in range(user_mark.mark):
                        possible_marks[key].discard(m)

        return {
            scale_in_topic.id:
                possible_marks[self._scale_in_topic_key(scale_in_topic)]
            for scale_in_topic in scale_in_topics
        }

    def _scale_in_topic_key(self, scale_in_topic):
        return '{}.{}'.format(scale_in_topic.topic.short_name,
                              scale_in_topic.scale.short_name)

    def update_by_level_dependencies(self):
        downward_dependencies = list(
                models.LevelDownwardDependency.objects.filter(source_level__questionnaire=self.questionnaire))
        upward_dependencies = list(
                models.LevelUpwardDependency.objects.filter(source_level__questionnaire=self.questionnaire))

        user_marks = models.UserMark.objects.filter(user=self.user,
                                                    scale_in_topic__topic__questionnaire=self.questionnaire)

        levels = {level.id: level for level in models.Level.objects.annotate(scales_count=Count('topic__scaleintopic'))}

        zero_marks_count_by_level = collections.defaultdict(int)
        max_marks_count_by_level = collections.defaultdict(int)
        for user_mark in user_marks.select_related('scale_in_topic__topic',
                                                   'scale_in_topic__scale_label_group__scale'):
            level_id = user_mark.scale_in_topic.topic.level_id
            if user_mark.mark == 0:
                zero_marks_count_by_level[level_id] += 1
            if user_mark.mark == user_mark.scale_in_topic.scale.max_mark:
                max_marks_count_by_level[level_id] += 1

        for dependency in downward_dependencies:
            max_marks_count = max_marks_count_by_level[dependency.source_level_id]
            if dependency.satisfy(max_marks_count, levels[dependency.source_level_id].scales_count):
                self.set_mark_for_all_topics_in_level(dependency.destination_level_id)

        for dependency in upward_dependencies:
            zero_marks_count = zero_marks_count_by_level[dependency.source_level_id]
            if dependency.satisfy(zero_marks_count, levels[dependency.source_level_id].scales_count):
                self.set_mark_for_all_topics_in_level(dependency.destination_level_id, 0)

    def set_mark_for_all_topics_in_level(self, destination_level_id, mark=None):
        """
        :param mark: put mark=None for setting maximum possible mark
        """
        for scale_in_topic in models.ScaleInTopic.objects.filter(topic__level_id=destination_level_id) \
                .select_related('scale_label_group__scale'):
            if mark is None:
                real_mark = scale_in_topic.scale_label_group.scale.max_mark
            else:
                real_mark = mark

            models.UserMark.objects.get_or_create(user=self.user,
                                                  scale_in_topic=scale_in_topic,
                                                  defaults={
                                                      'mark': real_mark,
                                                      'is_automatically': True,
                                                  })
