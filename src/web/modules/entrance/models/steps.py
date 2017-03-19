import enum

from django.db import models, transaction
from django.utils import timezone
from polymorphic import models as polymorphic_models

import questionnaire.models
import schools.models


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

    session = models.ForeignKey(
        schools.models.Session,
        related_name='+',
        help_text='Шаг будет показывать только зачисленным в эту смену',
        blank=True,
        null=True,
        default=None
    )

    parallel = models.ForeignKey(
        schools.models.Parallel,
        related_name='+',
        help_text='Шаг будет показывать только зачисленным в эту параллель',
        blank=True,
        null=True,
        default=None
    )

    visible_only_for_enrolled = models.BooleanField(
        default=False,
        blank=True,
        help_text='Шаг будет виден только зачисленным в школу пользователям',
    )

    order = models.PositiveIntegerField(
        help_text='Шаги упорядочиваются по возрастанию этого параметра'
    )

    available_from_time = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        help_text='Начиная с какого времени доступен шаг'
    )

    available_to_time = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        help_text='До какого времени доступен доступен шаг'
    )

    # TODO (andgein): Возможно, это должен быть ManyToManyField
    available_after_step = models.ForeignKey(
        'self',
        related_name='+',
        null=True,
        blank=True,
        default=None,
        help_text='Шаг доступен только при выполнении другого шага'
    )

    """
    Override to False in your subclass if you don't want to see background
    around you block
    """
    with_background = True

    """
    Override to False in your subclass for disabling timeline point
    at the left border of the timeline
    """
    with_timeline_point = True

    """ Override to True in your subclass to keep your step always open """
    always_expanded = False

    def is_passed(self, user):
        """
         Returns True if step is fully passed by user.
         If you override this method, don't forget call parent's is_passed().
         I.e.:
            def is_passed(self, user):
                return super().is_passed(user) and self.some_magic(user)
        """
        return True

    def is_visible(self, user):
        """
        Override to False in your subclass for invisible steps
        If you override this method, don't forget call parent's is_visible().
         I.e.:
            def is_visible(self, user):
                return super().is_visible(user) and self.some_magic(user)
        """
        return True

    def get_state(self, user):
        """
         Returns state of this step for user. You can override it in subclass
         :returns EntranceStepState
        """
        now = timezone.now()
        if (self.available_from_time is not None and
           now < self.available_from_time):
            return EntranceStepState.NOT_OPENED

        if (self.available_to_time is not None and
           self.available_to_time < now):
            return EntranceStepState.CLOSED

        if (self.available_after_step is not None and
           not self.available_after_step.is_passed(user)):
            return EntranceStepState.WAITING_FOR_OTHER_STEP

        if self.is_passed(user):
            return EntranceStepState.PASSED

        return EntranceStepState.NOT_PASSED

    def build(self, user):
        """
        You can override it in your subclass
        :return: EntranceStepBlock or None
        """
        if not self.is_visible(user):
            return None
        return EntranceStepBlock(self, user, self.get_state(user))

    @property
    def template_file(self):
        """
        Returns template filename (in templates/entrance/steps/) for this step.
        Override this property in your subclass.
        i.e.:
        class FooBarEntranceStep(AbstractEntranceStep):
            template_name = 'foo_bar.html'
        """
        return '%s.html' % self.__class__.__name__

    def save(self, *args, **kwargs):
        if (self.session is not None and
           self.session.school_id != self.school_id):
            raise ValueError('modules.entrance.models.AbstractEntranceStep: '
                             'session should belong to the same school as step')
        if (self.parallel is not None and
           self.parallel.school_id != self.school_id):
            raise ValueError('modules.entrance.models.AbstractEntranceStep: '
                             'parallel should belong to the same school as step')
        super().save(*args, **kwargs)


class EntranceStepTextsMixIn(models.Model):
    """
    Inherit your entrance step from EntranceStepTextsMixIn to get the following
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
        if (self.questionnaire_id is not None and
           self.questionnaire.school is not None and
           self.school_id != self.questionnaire.school_id):
            raise ValueError('entrance.steps.FillQuestionnaireEntranceStep: '
                             'questionnaire should belong to step\'s school')
        super().save(*args, **kwargs)

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
        if (self.exam is not None and
           self.school_id != self.exam.school_id):
            raise ValueError('entrance.steps.SolveExamEntranceStep: '
                             'exam should belong to step\'s school')
        super().save(*args, **kwargs)

    # Entrance exam is never passed. Mu-ha-ha!
    def is_passed(self, user):
        return False

    def __str__(self):
        return 'Шаг вступительной работы %s для %s' % (str(self.exam),
                                                       str(self.school))


class ResultsEntranceStep(AbstractEntranceStep):
    """
    Entrance step for show results (enrolled, not enrolled) and absence reason
    if exists (not confirmed, rejected, ...).
    """
    template_file = 'results.html'

    with_background = False
    with_timeline_point = False
    always_expanded = True

    def _get_visible_entrance_status(self, user):
        # It's here to avoid cyclic imports
        import modules.entrance.models as entrance_models

        return entrance_models.EntranceStatus.get_visible_status(
            self.school,
            user
        )

    def _get_absence_reason(self, user):
        # It's here to avoid cyclic imports
        import modules.entrance.models.main as entrance_models

        return (entrance_models.AbstractAbsenceReason
                .for_user_in_school(user, self.school))

    # TODO(andgein): cache calculated value
    def is_passed(self, user):
        if not super().is_passed(user):
            return False

        entrance_status = self._get_visible_entrance_status(user)
        absence_reason = self._get_absence_reason(user)
        return (entrance_status is not None and
                entrance_status.is_enrolled and
                absence_reason is None)

    def _get_entrance_message(self, entrance_status):
        if entrance_status.is_enrolled:
            if entrance_status.session is not None:
                session_name = str(entrance_status.session)
            else:
                session_name = self.school.name

            message = 'Поздравляем! Вы приняты в ' + session_name
            if entrance_status.parallel is not None:
                message += ' в параллель ' + entrance_status.parallel.name
        else:
            message = 'К сожалению, вы не приняты в ' + self.school.name
            if entrance_status.public_comment:
                message += '.\nПричина: ' + entrance_status.public_comment

        return message

    def build(self, user):
        block = super().build(user)

        entrance_status = self._get_visible_entrance_status(user)
        absence_reason = self._get_absence_reason(user)
        if entrance_status is not None:
            entrance_status.message = self._get_entrance_message(
                entrance_status)
            if absence_reason is not None:
                entrance_status.absence_reason = absence_reason

        block.entrance_status = entrance_status
        return block

    def __str__(self):
        return 'Шаг показа результатов поступления для ' + self.school.name


class MakeUserParticipatingEntranceStep(AbstractEntranceStep):
    """
    Invisible step for add record about participating user
    in school enrollment process. I.e. insert it before SolveExamEntranceStep
    """
    def is_visible(self, user):
        return False

    def build(self, user):
        # It's here to avoid cyclic imports
        import modules.entrance.models.main as entrance_models

        with transaction.atomic():
            current = entrance_models.EntranceStatus.objects.filter(
                school=self.school,
                user=user,
            ).first()
            if (current is None or
               current.status == entrance_models.EntranceStatus.Status.NOT_PARTICIPATED):
                entrance_models.EntranceStatus.create_or_update(
                    self.school,
                    user,
                    entrance_models.EntranceStatus.Status.PARTICIPATING
                )

        return super().build(user)

    def __str__(self):
        return 'Шаг, объявляющий школьника поступающим в ' + self.school.name
