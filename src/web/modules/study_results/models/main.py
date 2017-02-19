import djchoices
import polymorphic.models
from django.db import models

import schools.models
import users.models


class StudyResult(models.Model):
    class Evaluation(djchoices.DjangoChoices):
        NOT_APPLICABLE = djchoices.ChoiceItem('N/A', 'N/A')
        TWO = djchoices.ChoiceItem('2', '2')
        THREE_MINUS = djchoices.ChoiceItem('3-', '3-')
        THREE = djchoices.ChoiceItem('3', '3')
        THREE_PLUS = djchoices.ChoiceItem('3+', '3+')
        FOUR_MINUS = djchoices.ChoiceItem('4-', '4-')
        FOUR = djchoices.ChoiceItem('4', '4')
        FOUR_PLUS = djchoices.ChoiceItem('4+', '4+')
        FIVE_MINUS = djchoices.ChoiceItem('5-', '5-')
        FIVE = djchoices.ChoiceItem('5', '5')
        FIVE_PLUS = djchoices.ChoiceItem('5+', '5+')

    school = models.ForeignKey(schools.models.School,
                               related_name='study_results')

    user = models.ForeignKey(users.models.User, related_name='study_results')

    parallel = models.ForeignKey(schools.models.Parallel, null=True,
                                 related_name='study_results')
    # TODO: add group to school module
    # group = models.CharField(max_length=3, help_text='Например, C1')

    theory = models.CharField(max_length=3, choices=Evaluation.choices,
                              null=True, validators=[Evaluation.validator])

    practice = models.CharField(max_length=3, choices=Evaluation.choices,
                                null=True, validators=[Evaluation.validator])

    class Meta:
        unique_together = ('school', 'user')

    @classmethod
    def for_user_in_school(cls, user, school):
        return cls.objects.filter(user=user, school=school).first()

class AbstractComment(polymorphic.models.PolymorphicModel):
    study_result = models.ForeignKey(StudyResult, related_name='comments')

    comment = models.TextField(blank=True)

    created_by = models.ForeignKey(users.models.User, related_name='+',
                                   null=True, default=None, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type() + ': ' + self.comment

    def type(self):
        raise NotImplementedError()

class StudyComment(AbstractComment):
    def type(self):
        return 'Комментарий по учёбе'

class SocialComment(AbstractComment):
    def type(self):
        return 'Комментарий по внеучебной деятельности'

class WinterParticipationComment(AbstractComment):
    def type(self):
        return 'Брать ли в зиму'

class NextYearComment(AbstractComment):
    def type(self):
        return 'Куда брать в следующем году'

class AsTeacherComment(AbstractComment):
    def type(self):
        return 'Брать ли препом'

class WinterComment(AbstractComment):
    def type(self):
        return 'Комментарий с зимы'
