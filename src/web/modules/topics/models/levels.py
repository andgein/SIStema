from modules.entrance import models as entrance_models

from django.db import models as django_models


class EntranceLevelRequirement(django_models.Model):
    """
    Каждое требование задаётся кортежом (tag, max_penalty).
    Это значит, что сумма баллов школьника по всем шкалам всех тем с тегом tag должна отличаться
    от максимальной не более чем на max_penalty.
    """
    questionnaire = django_models.ForeignKey(
        'topics.TopicQuestionnaire',
        on_delete=django_models.CASCADE,
    )

    entrance_level = django_models.ForeignKey(
        entrance_models.EntranceLevel,
        on_delete=django_models.CASCADE,
    )

    tag = django_models.ForeignKey(
        'topics.Tag',
        on_delete=django_models.CASCADE,
    )

    max_penalty = django_models.PositiveIntegerField()

    class Meta:
        unique_together = ('questionnaire', 'entrance_level', 'tag')

    def __str__(self):
        return 'EntranceLevelRequirement(level: {}, tag: {}, max_penalty: {})'.format(
                    self.entrance_level.name, self.tag.title, self.max_penalty)

    def satisfy(self, sum_marks, max_marks):
        return max_marks - sum_marks <= self.max_penalty
