import datetime
import enum

from django.template import engines, Context
from django.utils.safestring import mark_safe
from django.db import models

from polymorphic import models as polymorphic_models

import schools.models
import questionnaire.models


class EntranceStepState(enum.Enum):
    NOT_OPENED = 1
    WAITING_FOR_OTHER_STEP = 2
    NOT_PASSED = 3
    PASSED = 4
    CLOSED = 5
    WARNING = 6

# See
# http://stackoverflow.com/questions/35953132/how-to-access-enum-types-in-django-templates
# for details
EntranceStepState.do_not_call_in_templates = True


class EntranceStepBlock:
    def __init__(self, step, user, state):
        self.step = step
        self.user = user
        self.state = state


class AbstractEntranceStep(polymorphic_models.PolymorphicModel):
    school = models.ForeignKey(
        schools.models.School,
        related_name='entrance_steps',
        help_text='Школа, к которой относится шаг'
    )

    order = models.PositiveIntegerField(
        help_text='Шаги упорядочиваются по возрастанию этого параметра'
    )

    available_from_date = models.DateField(
        null=True,
        blank=True,
        default=None,
        help_text='Начиная с какой даты доступен шаг'
    )

    # TODO(andgein): Может, это DateTimeField, а не DateField?
    available_to_date = models.DateField(
        null=True,
        blank=True,
        default=None,
        help_text='До какой даты доступен доступен шаг'
    )

    available_after_step = models.ForeignKey(
        'self',
        related_name='+',
        null=True,
        blank=True,
        default=None,
        help_text='Шаг доступен только при выполнении другого шага'
    )

    """
    Set to False if you don't want to see background around you block
    """
    with_background = True

    """
    Set to False for disabling timeline point at left border of the timeline
    """
    with_timeline_point = True

    """
    Set to False for invisible steps
    """
    visible = True

    def is_passed(self, user):
        """
         Returns True if step is fully passed by user.
         If you override this method, don't forget call parent's is_passed().
         I.e.:
            def is_passed(self, user):
                return super().is_passed(user) and self.some_magic(user)
        """
        return True

    def get_state(self, user):
        """
         Returns state of this step for user. You can override it in subclass
         :returns EntranceStepState
        """
        today = datetime.date.today()
        if self.available_from_date is not None and \
           today < self.available_from_date:
            return EntranceStepState.NOT_OPENED

        if self.available_to_date is not None and \
           self.available_to_date < today:
            return EntranceStepState.CLOSED

        if self.available_after_step is not None and \
           not self.available_after_step.is_passed(user):
            return EntranceStepState.WAITING_FOR_OTHER_STEP

        if self.is_passed(user):
            return EntranceStepState.PASSED

        return EntranceStepState.NOT_PASSED

    def build(self, user):
        """
        You can override it in your subclass
        :return: EntranceStepBlocks or None
        """
        if not self.visible:
            return None
        return EntranceStepBlock(self, user, self.get_state(user))

    @property
    def template_file(self):
        """
        Returns template filename (in templates/entrance/steps) for this step.
        Override this property in your subclass.
        i.e.:
        class FooBarEntranceStep(AbstractEntranceStep):
            template_name = 'foo_bar.html'
        """
        return '%s.html' % self.__class__.__name__


class EntranceStepTextsMixIn(models.Model):
    """
    Inherit your entrance step from EntranceStepTextsMixIn to get follow
    TextFields in your model:
    * text_before_start_date
    * text_after_finish_date
    * text_required_step_is_not_passed
    * text_step_is_not_passed
    * text_step_is_passed
    """

    text_before_start_date = models.TextField(
        help_text='Текст, который показывается до даты начала заполнения шага. '
                  'Поддерживается Markdown',
        blank=True
    )

    text_after_finish_date = models.TextField(
        help_text='Текст, который показывается после даты окончания заполнения. '
                  'Поддерживается Markdown',
        blank=True
    )

    text_waiting_for_other_step = models.TextField(
        help_text='Текст, который показывается, когда не пройден один из'
                  'предыдущих шагов. Поддерживается Markdown',
        blank=True
    )

    text_step_is_not_passed = models.TextField(
        help_text='Текст, который показывается, когда шаг ещё не пройден. '
                  'Поддерживается Markdown',
        blank=True
    )

    text_step_is_passed = models.TextField(
        help_text='Текст, который показывается, '
                  'когда шаг пройден пользователем. Поддерживается Markdown',
        blank=True
    )

    class Meta:
        abstract = True


class ConfirmProfileEntranceStep(AbstractEntranceStep, EntranceStepTextsMixIn):
    template_file = 'confirm_profile.html'

    def __str__(self):
        return 'Шаг подтверждения профиля для %s' % (str(self.school),)


class FillQuestionnaireEntranceStep(AbstractEntranceStep,
                                    EntranceStepTextsMixIn):
    template_file = 'fill_questionnaire.html'

    questionnaire = models.ForeignKey(
        questionnaire.models.Questionnaire,
        help_text='Анкета, которую нужно заполнить',
        related_name='+'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.questionnaire_id is not None and \
           self.questionnaire.school is not None and \
           self.school_id != self.questionnaire.school_id:
            raise ValueError('entrance.steps.FillQuestionnaireEntranceStep: '
                             'questionnaire should belong to step\'s school')

    def is_passed(self, user):
        return super().is_passed(user) and self.questionnaire.is_filled_by(user)

    def __str__(self):
        return 'Шаг заполнения анкеты %s для %s' % (str(self.questionnaire),
                                                    str(self.school))


class SolveExamEntranceStep(AbstractEntranceStep, EntranceStepTextsMixIn):
    template_file = 'solve_exam.html'

    exam = models.ForeignKey(
        'entrance.EntranceExam',
        help_text='Вступительная работа, которую нужно решить',
        related_name='+'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.exam.school_id is not None and \
           self.school_id != self.exam.school_id:
            raise ValueError('entrance.steps.SolveExamEntranceStep: '
                             'exam should belong to step\'s school')

    # Entrance exam is never passed. Mu-ha-ha!
    def is_passed(self, user):
        return False

    def __str__(self):
        return 'Шаг вступительной работы %s для %s' % (str(self.exam),
                                                       str(self.school))


class ResultsEntranceStep(AbstractEntranceStep):
    template_file = 'results.html'

    with_background = False
    with_timeline_point = False

    def _get_visible_entrance_status(self, user):
        # It's here to avoid cyclic imports
        import modules.entrance.models.main as entrance_models

        qs = entrance_models.EntranceStatus.objects.filter(
            school=self.school,
            user=user,
            is_status_visible=True
        )
        entrance_status = None
        if qs.exists():
            entrance_status = qs.first()
            entrance_status.is_enrolled = entrance_status.status == \
                entrance_models.EntranceStatus.Status.ENROLLED
        return entrance_status

    # TODO (andgein): cache calculated state
    def get_state(self, user):
        state = super().get_state(user)

        if state == EntranceStepState.NOT_PASSED:
            entrance_status = self._get_visible_entrance_status(user)
            if entrance_status.is_enrolled:
                return EntranceStepState.PASSED
        return state

    def build(self, user):
        block = super().build(user)

        entrance_status = self._get_visible_entrance_status(user)
        if entrance_status is not None:
            if entrance_status.is_enrolled:
                entrance_status.message = \
                    'Поздравляем! Вы приняты в %s, в параллель %s смены %s' % (
                        self.school.name,
                        entrance_status.parallel.name,
                        entrance_status.session.name
                    )
            else:
                entrance_status.message = \
                    'К сожалению, вы не приняты в %s' % (self.school.name, )
                if entrance_status.public_comment:
                    entrance_status.message += \
                        '.\nПричина: %s' % (entrance_status.public_comment, )

        block.entrance_status = entrance_status
        return block

    def __str__(self):
        return 'Шаг показа результатов поступления для %s' % (str(self.school),)
