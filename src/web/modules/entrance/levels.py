from questionnaire.models import QuestionnaireAnswer, ChoiceQuestionnaireQuestionVariant
from . import models


class EntranceLevelLimiter:
    def __init__(self, school):
        self.school = school

    def _find_minimal_level(self):
        return models.EntranceLevel.objects.filter(school=self.school).order_by('order').first()

    def get_limit(self, user):
        raise NotImplementedError('modules.entrance.levels.EntranceLevelLimiter: Child must implement get_limit()')


class EntranceLevelLimit:
    def __init__(self, min_level):
        self.min_level = min_level

    def update_with_other(self, other_limit):
        if self.min_level is None:
            self.min_level = other_limit.min_level
            return

        if other_limit.min_level is not None:
            if self.min_level < other_limit.min_level:
                self.min_level = other_limit.min_level


class AlreadyWasEntranceLevelLimiter(EntranceLevelLimiter):
    # TODO: move it to settings?
    question_short_name = 'previous_parallels'

    def get_limit(self, user):
        qs = QuestionnaireAnswer.objects.filter(
            questionnaire__school=self.school,
            user=user,
            question_short_name=self.question_short_name
        )
        if not qs.exists():
            return EntranceLevelLimit(self._find_minimal_level())

        answers = list(qs)
        variants = list(ChoiceQuestionnaireQuestionVariant.objects.filter(
                question__questionnaire__school=self.school,
                question__short_name=self.question_short_name
        ))
        answers = [a.answer for a in answers]
        variants = [v.text for v in variants if str(v.id) in answers]

        levels = models.EntranceLevel.objects.filter(school=self.school)
        if 'A' in variants or 'AS' in variants or 'AA' in variants or 'A\'' in variants or 'AY' in variants:
            return EntranceLevelLimit(levels.filter(short_name='a').get())
        if 'B' in variants or 'P' in variants:
            return EntranceLevelLimit(levels.filter(short_name='a_prime').get())
        if 'B\'' in variants:
            return EntranceLevelLimit(levels.filter(short_name='b').get())
        if 'C' in variants:
            return EntranceLevelLimit(levels.filter(short_name='b_prime').get())
        if 'C\'' in variants:
            return EntranceLevelLimit(levels.filter(short_name='c').get())
        if 'D' in variants:
            return EntranceLevelLimit(levels.filter(short_name='c_prime').get())

        return EntranceLevelLimit(self._find_minimal_level())


class AgeEntranceLevelLimiter(EntranceLevelLimiter):
    def get_limit(self, user):
        if not hasattr(user, 'user_profile'):
            return EntranceLevelLimit(self._find_minimal_level())

        current_class = user.user_profile.current_class
        if current_class is None:
            return EntranceLevelLimit(self._find_minimal_level())

        levels = models.EntranceLevel.objects.filter(school=self.school)

        if current_class >= 10:
            return EntranceLevelLimit(levels.filter(short_name='b_prime').get())
        if current_class == 9:
            return EntranceLevelLimit(levels.filter(short_name='c').get())
        if current_class == 8:
            return EntranceLevelLimit(levels.filter(short_name='c_prime').get())

        return EntranceLevelLimit(self._find_minimal_level())

