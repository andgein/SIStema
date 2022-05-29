from django.db import models
import djchoices
import polymorphic.models

import schools.models
import users.models


class StudyResult(models.Model):
    class Evaluation(djchoices.DjangoChoices):
        NOT_APPLICABLE = djchoices.ChoiceItem('N/A', 'N/A')
        TWO = djchoices.ChoiceItem('2', '2')
        TWO_PLUS = djchoices.ChoiceItem('2+', '2+')
        THREE_MINUS = djchoices.ChoiceItem('3-', '3-')
        THREE = djchoices.ChoiceItem('3', '3')
        THREE_PLUS = djchoices.ChoiceItem('3+', '3+')
        FOUR_MINUS = djchoices.ChoiceItem('4-', '4-')
        FOUR = djchoices.ChoiceItem('4', '4')
        FOUR_PLUS = djchoices.ChoiceItem('4+', '4+')
        FIVE_MINUS = djchoices.ChoiceItem('5-', '5-')
        FIVE = djchoices.ChoiceItem('5', '5')
        FIVE_PLUS = djchoices.ChoiceItem('5+', '5+')
        FIVE_PLUS_PLUS = djchoices.ChoiceItem('5++', '5++')

    school_participant = models.OneToOneField(
        schools.models.SchoolParticipant,
        on_delete=models.CASCADE,
        related_name='study_result',
    )

    theory = models.CharField(max_length=3, choices=Evaluation.choices,
                              null=True, validators=[Evaluation.validator])

    practice = models.CharField(max_length=3, choices=Evaluation.choices,
                                null=True, validators=[Evaluation.validator])


class AbstractComment(polymorphic.models.PolymorphicModel):
    study_result = models.ForeignKey(
        StudyResult,
        on_delete=models.CASCADE,
        related_name='comments',
    )

    comment = models.TextField(blank=True)

    created_by = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='+',
        null=True,
        default=None,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.verbose_type() + ': ' + self.comment

    def verbose_type(self):
        raise NotImplementedError()


class StudyComment(AbstractComment):
    def verbose_type(self):
        return 'Учёба'


class SocialComment(AbstractComment):
    def verbose_type(self):
        return 'Внеучебная деятельность'


class AsWinterParticipantComment(AbstractComment):
    def verbose_type(self):
        return 'Брать ли в зиму'


class NextYearComment(AbstractComment):
    def verbose_type(self):
        return 'Куда брать в следующем году'


class AsTeacherComment(AbstractComment):
    def verbose_type(self):
        return 'Брать ли препом'


class AfterWinterComment(AbstractComment):
    def verbose_type(self):
        return 'Комментарий с зимы'
