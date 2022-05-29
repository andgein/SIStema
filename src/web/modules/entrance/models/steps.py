import enum
import operator
from typing import Optional

from cached_property import cached_property
from django.core.exceptions import ValidationError
from django.db import models, transaction, IntegrityError
from django.conf import settings
from polymorphic import models as polymorphic_models

import groups.models
import questionnaire.models
import schools.models
from . import main as main_models
from . import levels as levels_models
from .. import forms


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
    def __init__(self, step: "AbstractEntranceStep", user, state):
        self.step = step
        self.user = user
        self.state = state

        # Pre-compute step fields for the particular user to be used in
        # templates
        self.step_available_from_time = (
            None if step.available_from_time is None
            else step.available_from_time.datetime_for_user(user))
        self.step_available_to_time = (
            None if step.available_to_time is None
            else step.available_to_time.datetime_for_user(user))
        self.step_is_opened = step.is_opened(user)
        self.step_is_closed = step.is_closed(user)

        next_visible_step = step.get_next_visible_step(user)
        self.step_is_last_passed_step = step.is_passed(user) and (
            next_visible_step is None or not next_visible_step.is_passed(user)
        )


class AbstractEntranceStep(polymorphic_models.PolymorphicModel):
    school = models.ForeignKey(
        schools.models.School,
        on_delete=models.CASCADE,
        related_name='entrance_steps',
        help_text='Школа, к которой относится шаг',
    )

    session = models.ForeignKey(
        schools.models.Session,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Шаг будет показывать только зачисленным в эту смену',
        blank=True,
        null=True,
        default=None,
    )

    parallel = models.ForeignKey(
        schools.models.Parallel,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Шаг будет показывать только зачисленным в эту параллель',
        blank=True,
        null=True,
        default=None,
    )

    visible_only_for_enrolled = models.BooleanField(
        default=False,
        blank=True,
        help_text='Шаг будет виден только зачисленным в школу пользователям',
    )

    order = models.PositiveIntegerField(
        help_text='Шаги упорядочиваются по возрастанию этого параметра'
    )

    available_from_time = models.ForeignKey(
        'dates.KeyDate',
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
        blank=True,
        verbose_name='Доступен с',
    )

    available_to_time = models.ForeignKey(
        'dates.KeyDate',
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
        blank=True,
        verbose_name='Доступен до',
    )

    # TODO (andgein): Возможно, это должен быть ManyToManyField
    available_after_step = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='+',
        null=True,
        blank=True,
        default=None,
        help_text='Шаг доступен только при выполнении другого шага',
    )

    class Meta:
        verbose_name = 'entrance step'

    """
    Override to False in your subclass if you don't want to see background
    around you block
    """
    with_background = True

    """ Override to True in your subclass to keep your step always open """
    always_expanded = False

    @cached_property
    def _available_from_time(self):
        return self.available_from_time

    @cached_property
    def _available_to_time(self):
        return self.available_to_time

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
         Returns state of this step for user. You can override it in subclass,
         but do it carefully please.
         `get_state()` should always return EntranceStepState.
          If step is closed by time, return NOT_OPENED or NOT_CLOSED.
          If previous step is not passed return WAITING_FOR_OTHER_STEP

          If you want just override PASSED/NOT_PASSED selection, don't override
          `get_state`, override `is_passed` instead of it.
         :returns EntranceStepState
        """
        if not self.is_opened(user):
            return EntranceStepState.NOT_OPENED

        if (self.available_after_step is not None and
            self.available_after_step.get_state(user) != EntranceStepState.PASSED):
            return EntranceStepState.WAITING_FOR_OTHER_STEP

        if self.is_passed(user):
            return EntranceStepState.PASSED

        if self.is_closed(user):
            return EntranceStepState.CLOSED

        return EntranceStepState.NOT_PASSED

    def build(self, user, request):
        """
        You can override it in your subclass
        :returns EntranceStepBlock or None
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
            raise IntegrityError(
                'AbstractEntranceStep: '
                'session should belong to the same school as step'
            )
        if (self.parallel is not None and
           self.parallel.school_id != self.school_id):
            raise IntegrityError(
                'AbstractEntranceStep: '
                'parallel should belong to the same school as step'
            )
        super().save(*args, **kwargs)

    def is_opened(self, user):
        if self._available_from_time is None:
            return True
        return self._available_from_time.passed_for_user(user)

    def is_closed(self, user):
        if self._available_to_time is None:
            return False
        return self._available_to_time.passed_for_user(user)

    @property
    def next(self) -> Optional["AbstractEntranceStep"]:
        return self.school.entrance_steps.filter(order__gt=self.order).order_by("order").first()

    def get_next_visible_step(self, user) -> Optional["AbstractEntranceStep"]:
        next_step = self.next
        while next_step is not None and not next_step.is_visible(user):
            next_step = next_step.next
        return next_step


class EntranceStepTextsMixIn(models.Model):
    """
    Inherit your entrance step from EntranceStepTextsMixIn to get the following
    TextFields in your model:
    * text_before_start_date
    * text_after_finish_date_if_passed
    * text_after_finish_date_if_not_passed
    * text_required_step_is_not_passed
    * text_step_is_not_passed
    * text_step_is_passed
    """

    text_before_start_date = models.TextField(
        help_text='Текст, который показывается до даты начала заполнения шага. '
                  'Поддерживается Markdown',
        blank=True
    )

    text_after_finish_date_if_passed = models.TextField(
        help_text='Текст, который показывается после даты окончания заполнения, '
                  'если шаг выполнен. Поддерживается Markdown',
        blank=True
    )

    text_after_finish_date_if_not_passed = models.TextField(
        help_text='Текст, который показывается после даты окончания заполнения, '
                  'если шаг не выполнен. Поддерживается Markdown',
        blank=True
    )

    text_waiting_for_other_step = models.TextField(
        help_text='Текст, который показывается, когда не пройден один '
                  'из предыдущих шагов. Поддерживается Markdown',
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

    def is_passed(self, user):
        available_from_for_user = (
            self.available_from_time.datetime_for_user(user))
        return (super().is_passed(user) and
                user.profile.updated_at >= available_from_for_user)

    def __str__(self):
        return 'Шаг подтверждения профиля для ' + self.school.name


class EnsureProfileIsFullEntranceStep(AbstractEntranceStep, EntranceStepTextsMixIn):
    template_file = 'ensure_profile_is_full.html'

    def is_passed(self, user):
        if not super().is_passed(user):
            return False
        if not hasattr(user, 'profile'):
            return False
        profile = user.profile
        return profile.is_fully_filled()

    def __str__(self):
        return 'Шаг полного заполнения профиля для ' + self.school.name


class FillQuestionnaireEntranceStep(AbstractEntranceStep,
                                    EntranceStepTextsMixIn):
    template_file = 'fill_questionnaire.html'

    questionnaire = models.ForeignKey(
        questionnaire.models.Questionnaire,
        on_delete=models.CASCADE,
        help_text='Анкета, которую нужно заполнить',
        related_name='+',
    )

    def save(self, *args, **kwargs):
        if (self.questionnaire_id is not None and
           self.questionnaire.school is not None and
           self.school_id != self.questionnaire.school_id):
            raise IntegrityError(
                'FillQuestionnaireEntranceStep: '
                'questionnaire should belong to the same school as step'
            )
        super().save(*args, **kwargs)

    def is_passed(self, user):
        return super().is_passed(user) and self.questionnaire.is_filled_by(user)

    def __str__(self):
        return 'Шаг заполнения анкеты «{}» для {}'.format(
            self.questionnaire,
            self.school
        )


class SolveExamEntranceStep(AbstractEntranceStep, EntranceStepTextsMixIn):
    template_file = 'solve_exam.html'

    exam = models.ForeignKey(
        'entrance.EntranceExam',
        on_delete=models.CASCADE,
        help_text='Вступительная работа, которую нужно решить',
        related_name='+'
    )

    def save(self, *args, **kwargs):
        if (self.exam is not None and
           self.school_id != self.exam.school_id):
            raise IntegrityError(
                'entrance.steps.SolveExamEntranceStep: '
                'exam should belong to step\'s school'
            )
        super().save(*args, **kwargs)

    def is_passed(self, user):
        return super().is_passed(user) and self.is_closed(user)

    @staticmethod
    def _get_accepted_count(tasks):
        return len(list(filter(lambda t: t.is_accepted, tasks)))

    def build(self, user, request):
        # It's here to avoid cyclic imports
        import modules.entrance.views as entrance_views
        import modules.entrance.upgrades as entrance_upgrades

        block = super().build(user, request)
        level, tasks = entrance_views.get_entrance_level_and_tasks(self.school, user)

        for task in tasks:
            task.is_accepted = task.is_accepted_for_user(user)
            task.is_solved = task.is_solved_by_user(user)

        categories = list(sorted(
            {task.category for task in tasks},
            key=operator.attrgetter('order'),
        ))
        categories_with_tasks = [
            (category, [task for task in tasks if task.category == category])
            for category in categories
        ]

        entrance_exam = self.exam
        block.can_select_entrance_level = (
            not entrance_exam.is_closed(user) and
            entrance_exam.can_participant_select_entrance_level
        )
        if block.can_select_entrance_level:
            base_level = entrance_upgrades.get_base_entrance_level(self.school, user)
            block.selected_entrance_level = (
                entrance_views.get_entrance_level_selected_by_user(
                    self.school, user, base_level
                )
            )

            if request.GET.get('change_selected_entrance_level'):
                block.selected_entrance_level = None

            block.recommended_entrance_level = None
            if block.selected_entrance_level is None:
                block.recommended_entrance_level = entrance_upgrades.get_recommended_entrance_level(self.school, user)
                if block.recommended_entrance_level < base_level or block.recommended_entrance_level.is_maximal():
                    block.recommended_entrance_level = None

                block.select_entrance_level_form = forms.SelectEntranceLevelForm(
                    levels=list(self.school.entrance_levels.all()),
                    base_level=base_level,
                    recommended_level=block.recommended_entrance_level,
                )

        block.task_category_stats = []
        for category, tasks in categories_with_tasks:
            accepted_count = self._get_accepted_count(tasks)
            block.task_category_stats.append({
                'category': category,
                'is_started': category.is_started_for_user(user),
                'total_count': len(tasks),
                'solved_count': accepted_count,
                'needs_attention': category.is_mandatory and accepted_count == 0,
            })

        block.level = entrance_upgrades.get_maximum_issued_entrance_level(
            self.school,
            user,
            level
        )
        block.is_at_maximum_level = entrance_upgrades.is_user_at_maximum_level(
            self.school,
            user,
            level
        )

        return block

    def __str__(self):
        return 'Шаг вступительной работы {} для {}'.format(
            self.exam,
            self.school
        )


class ResultsEntranceStep(AbstractEntranceStep):
    """
    Entrance step for show results (enrolled, not enrolled) and absence reason
    if exists (not confirmed, rejected, ...).
    """
    template_file = 'results.html'

    with_background = False
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
            sessions_and_parallels = entrance_status.sessions_and_parallels.all()
            selected = sessions_and_parallels.filter(selected_by_user=True).first()
            if selected is not None:
                session_name = selected.session.get_full_name()
                parallel_name = selected.parallel.name if selected.parallel else ''
            else:
                if sessions_and_parallels.values('session').distinct().count() == 1:
                    session_name = sessions_and_parallels.first().session.get_full_name()
                else:
                    session_name = self.school.name

                if sessions_and_parallels.values('parallel').distinct().count() == 1:
                    parallel_name = sessions_and_parallels.first().parallel.name
                else:
                    parallel_name = ''

            message = 'Поздравляем! Вы приняты в ' + session_name
            if parallel_name:
                message += ' в параллель ' + parallel_name
        elif entrance_status.is_in_reserve_list:
            message = ('Вы находитесь в резервном списке на поступление. '
                       'Вы будете зачислены в ' + self.school.name + ' ' +
                       'в случае появления свободных мест. '
                       'К сожалению, мы не можем гарантировать, '
                       'что это произойдёт.')
            if entrance_status.public_comment:
                message += '\nПричина: ' + entrance_status.public_comment
        else:
            message = 'К сожалению, вы не приняты в ' + self.school.name
            if entrance_status.public_comment:
                message += '.\nПричина: ' + entrance_status.public_comment

        return message

    def build(self, user, request):
        block = super().build(user, request)

        entrance_status = self._get_visible_entrance_status(user)
        absence_reason = self._get_absence_reason(user)
        if entrance_status is not None:
            entrance_status.message = self._get_entrance_message(entrance_status)
            if absence_reason is not None:
                entrance_status.absence_reason = absence_reason
                block.title = 'Вы отказались от участия в ' + self.school.name

            if absence_reason is None and entrance_status.is_enrolled:
                block.title = 'Вы приняты в ' + self.school.name

            sessions_and_parallels = entrance_status.sessions_and_parallels.all()
            selected_variant = sessions_and_parallels.filter(selected_by_user=True).first()

            block.has_multiple_variants = len(sessions_and_parallels) > 1
            block.has_selected_variant = selected_variant is not None

            block.should_choose = block.has_multiple_variants and not block.has_selected_variant
            block.can_reset = block.has_multiple_variants and block.has_selected_variant and (
                self.available_to_time is None or not self.available_to_time.passed_for_user(user)
            )
            block.should_approve = not block.has_multiple_variants and not block.has_selected_variant
            block.is_simple_approved = not block.has_multiple_variants and block.has_selected_variant

            block.select_session_and_parallel_form = forms.SelectSessionAndParallelForm(sessions_and_parallels)

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

    def build(self, user, request):
        # It's here to avoid cyclic imports
        import modules.entrance.models.main as entrance_models

        if self.get_state(user) == EntranceStepState.PASSED:
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

        return super().build(user, request)

    def __str__(self):
        return 'Шаг, объявляющий школьника поступающим в ' + self.school.name


class UserParticipatedInSchoolEntranceStep(AbstractEntranceStep,
                                           EntranceStepTextsMixIn):
    """
    Step considered as passed only if a user has participated in a specified
    school.

    Visible only if not passed.
    """

    template_file = 'user_participated_in_school.html'

    school_to_check_participation = models.ForeignKey(
        schools.models.School,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Шаг будет считаться пройденным только если пользователь '
                  'принимал участие в этой школе',
    )

    def __str__(self):
        return 'Шаг проверки участия в {} для {}'.format(
            self.school_to_check_participation, self.school)

    def is_visible(self, user):
        return not self.is_passed(user)

    def is_passed(self, user):
        return (
               user.school_participations
                   .filter(school=self.school_to_check_participation)
                   .exists()
           ) or (
               self.exceptions
                   .filter(user_id=user.id)
                   .exists()
           )

    def build(self, user, request):
        block = super().build(user, request)
        # block may be equal to None if it's invisible to the current user
        if block is not None:
            block.school_to_check_participation = (
                self.school_to_check_participation)
        return block


class UserParticipatedInSchoolEntranceStepException(models.Model):
    """
    Exception for UserParticipatedInSchoolEntranceStep. For the specified user
    the step considered passed regardless of the participation in the
    corresponding school.
    """
    step = models.ForeignKey(
        'UserParticipatedInSchoolEntranceStep',
        on_delete=models.CASCADE,
        related_name='exceptions',
        help_text='Шаг, для которого предназначено данное исключение',
    )

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Пользователь, для которого шаг считается выполненным, даже '
                  'если он не участвовал в соответствующей школе',
    )

    def __str__(self):
        return (
            'Исключение для пользователя {} в шаге проверки участия в {} для {}'
                .format(self.user,
                        self.step.school_to_check_participation,
                        self.step.school)
        )


class UserIsMemberOfGroupEntranceStep(AbstractEntranceStep,
                                      EntranceStepTextsMixIn):
    """
    Step considered as passed only if a user is a member of the specified group.

    Visible only if user is not a member of the group.
    """

    template_file = 'user_is_member_of_group.html'

    group = models.ForeignKey(
        groups.models.AbstractGroup,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Шаг будет считаться пройденным только если пользователь '
                  'состоит в группе. Пройденный шаг невидим.',
    )

    def __str__(self):
        return 'Шаг проверки, состоит ли пользователь в группе "{}" для {}' \
            .format(self.group.name, self.school)

    def is_visible(self, user):
        return not self.group.is_user_in_group(user)

    def is_passed(self, user):
        return self.group.is_user_in_group(user)

    def build(self, user, request):
        block = super().build(user, request)
        # block may be equal to None if it's invisible to the current user
        if block is not None:
            block.group = self.group
        return block


class MarkdownEntranceStep(AbstractEntranceStep, EntranceStepTextsMixIn):
    """
    Simple entrance step for showing markdown-rendered text. Supports
    `available_from_time` and `available_to_time` as well as
    `EntranceStepTextsMixIn`. Shows `markdown` field to everyone
    if corresponding mixin's text is empty.
    """
    template_file = 'markdown.html'

    always_expanded = True
    with_background = False

    markdown = models.TextField(
        help_text='Текст, который будет показан школьникам. '
                  'Поддерживается Markdown',
        blank=False,
    )

    def __str__(self):
        return 'Маркдаун-шаг для {}: «{}...»'.format(
            self.school,
            self.markdown[:20]
        )


class SelectEnrollmentTypeEntranceStep(AbstractEntranceStep, EntranceStepTextsMixIn):
    """
    Entrance step for choosing enrollment type: with entrance exam,
    auto-enrollment etc. Creates moderation request for some options.
    Options are described in EnrollmentType model.
    """
    template_file = 'select_enrollment_type.html'

    with_background = False

    text_on_moderation = models.TextField(
        help_text='Текст, который показывается пользователю, пока выбранный вариант '
                  'находится на модерации. Поддерживается Markdown'
    )

    text_passed_moderation = models.TextField(
        help_text='Текст, который показывается пользователю, когда выбранный вариант '
                  'прошёл модерацию. Поддерживается Markdown'
    )

    text_failed_moderation = models.TextField(
        help_text='Текст, который показывается пользователю, когда выбранный вариант '
                  'не прошёл модерацию. Поддерживается Markdown'
    )

    review_info = models.TextField(
        verbose_name='информация для модераторов',
        blank=True,
        default='',
        help_text='Поддерживается Markdown',
    )

    def __str__(self):
        return 'Шаг выбора способа поступления для {}'.format(self.school)

    def is_passed(self, user):
        if not super().is_passed(user):
            return False

        # Looking for enrollment type already selected in this step by the user
        selected = SelectedEnrollmentType.objects.filter(
            user=user,
            enrollment_type__step=self
        ).first()

        # If user doesn't select the enrollment type, step is not passed
        if selected is None:
            return False

        # If selected enrollment type doesn't need moderation, step is passed
        if not selected.enrollment_type.needs_moderation:
            return True

        return selected.is_approved

    def build(self, user, request):
        block = super().build(user, request)

        selected = SelectedEnrollmentType.objects.filter(
            user=user,
            step=self,
        ).first()
        block.selected = selected

        initial = {}
        form_enrollment_types = self.enrollment_types.all()
        if selected is not None:
            initial = {'enrollment_type': selected.enrollment_type_id}
            form_enrollment_types = [selected.enrollment_type]

        block.form = forms.SelectEnrollmentTypeForm(
            form_enrollment_types,
            disabled=selected is not None,
            initial=initial,
        )

        block.is_moderating = selected is not None and not selected.is_moderated
        block.passed_moderation = (
            selected is not None
            and selected.enrollment_type.needs_moderation
            and selected.is_moderated
            and selected.is_approved)
        block.failed_moderation = (
            selected is not None
            and selected.enrollment_type.needs_moderation
            and selected.is_moderated
            and not selected.is_approved)

        return block


class EnrollmentType(models.Model):
    step = models.ForeignKey(
        SelectEnrollmentTypeEntranceStep,
        on_delete=models.CASCADE,
        related_name='enrollment_types',
    )

    text = models.TextField(
        help_text='Например, «По вступительной работе»',
    )

    needs_moderation = models.BooleanField(
        help_text='Нужна ли модерация, если пользователь выбрал этот тип поступления',
    )

    def __str__(self):
        return 'Поступление {} для {}'.format(self.text, self.step.school)


class SelectedEnrollmentType(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )

    step = models.ForeignKey(
        SelectEnrollmentTypeEntranceStep,
        on_delete=models.CASCADE,
        related_name='+',
    )

    enrollment_type = models.ForeignKey(
        EnrollmentType,
        on_delete=models.CASCADE,
        related_name='selections',
    )

    is_moderated = models.BooleanField(
        help_text='Обработана ли заявка',
        db_index=True,
    )

    is_approved = models.BooleanField(
        help_text='Одобрена ли заявка',
        db_index=True,
    )

    parallel = models.ForeignKey(
        'schools.Parallel',
        on_delete=models.CASCADE,
        verbose_name='параллель',
        related_name='+',
        null=True,
        blank=True,
        help_text="Параллель, в которую школьник зачислен без выполнения "
                  "вступительной",
    )

    accepted_entrance_level = models.ForeignKey(
        levels_models.EntranceLevel,
        on_delete=models.CASCADE,
        verbose_name='зачтенный уровень вступительной',
        help_text='Зачтённый уровень вступительной. Задачи этого уровня школьнику '
                  'решать не надо, они зачтены автоматически. Должно коррелировать с '
                  'выданным уровнем вступительной (см. ниже)',
        related_name='+',
        default=None,
        blank=True,
        null=True,
    )

    entrance_level = models.ForeignKey(
        levels_models.EntranceLevel,
        on_delete=models.CASCADE,
        verbose_name='уровень вступительной',
        help_text='[Устарело, используйте «зачтённый уровень вступительной»] '
                  'Выставленный уровень вступительной. Должен содержать '
                  'задачи, необходимые для поступления в следующую параллель '
                  'после той, в которую школьник зачислен автоматически. '
                  'Если не указать, то автоматически посчитается как уровень, '
                  'следующий за «зачтённый уровень вступительной»',
        related_name='+',
        default=None,
        blank=True,
        null=True,
    )

    allow_pass_entrance_exam = models.BooleanField(
        verbose_name='разрешить ли сдавать вступительную',
        help_text='Если False, то школьнику будет недоступно выполнение вступительной работы ни на каком уровне. '
                  'Технически эквивалентно тому, чтобы выставить «зачтённый уровень вступительной» в максимально '
                  'возможный уровень. Отличается в формулировках, видимых пользователю.',
        default=True,
        null=False,
    )

    custom_resolution_text = models.TextField(
        help_text='Текст, объясняющий решение организаторов. Можно не указывать, '
                  'тогда школьнику покажется текст по умолчанию в зависимости '
                  'от того, одобрена ли заявка. Поддерживается Markdown',
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='модератор',
        null=True,
        help_text="Пользователь, который одобрил или отклонил заявку",
    )

    reviewed_at = models.DateTimeField(
        verbose_name='время модерации',
        null=True,
        blank=True,
        default=None,
        help_text='Когда заявка была рассмотрена',
    )

    class Meta:
        unique_together = ('user', 'step')

    def __str__(self):
        return '{} поступает в {}. {}'.format(
            self.user, self.step.school, self.enrollment_type
        )

    def has_entrance_level(self):
        return (
            self.accepted_entrance_level is not None or
            self.entrance_level is not None or
            not self.allow_pass_entrance_exam
        )

    def get_entrance_level(self):
        """
        Returns entrance level for participant.
        """
        if not self.allow_pass_entrance_exam:
            return levels_models.EntranceLevel.get_max_entrance_level(self.step.school)

        if self.accepted_entrance_level is not None:
            entrance_level = levels_models.EntranceLevel.objects.filter(
                school=self.step.school,
                order__gt=self.accepted_entrance_level.order,
            ).order_by('order').first()
            if entrance_level is not None:
                return entrance_level
            return levels_models.EntranceLevel.get_max_entrance_level(self.step.school)

        # Field entrance_level is deprecated, but watch it too
        # for backward compatibility
        if self.entrance_level is not None:
            return self.entrance_level

    def clean(self):
        if (self.entrance_level is not None and
           self.enrollment_type.step.school_id != self.entrance_level.school_id):
            raise ValidationError('Can\'t save SelectedEnrollmentType: '
                                  'Entrance step should belong to the same school '
                                  'as entrance level')
        if self.enrollment_type.step_id != self.step_id:
            raise ValidationError('Can\'t save SelectedEnrollmentType: '
                                  'Enrollment type should belong to the same step '
                                  'as this object')
        if self.accepted_entrance_level is not None and self.entrance_level is not None:
            raise ValidationError('Can\' specify both entrance_level and accepted_entrance_level. '
                                  'Choose only one.')
        if self.accepted_entrance_level is not None and not self.allow_pass_entrance_exam:
            raise ValidationError('Can\'t specify accepted_entrance_level while disallowing '
                                  'participating in the entrance exam. Left accepted_entrance_level '
                                  'empty.')
        if self.entrance_level is not None and not self.allow_pass_entrance_exam:
            raise ValidationError('Can\'t specify entrance_level while disallowing '
                                  'participating in the entrance exam. Left entrance_level '
                                  'empty.')

    def save(self, *args, **kwargs):
        if (self.entrance_level is not None and
           self.enrollment_type.step.school_id != self.entrance_level.school_id):
            raise IntegrityError('Can\'t save SelectedEnrollmentType: '
                                 'Entrance step should belong to the same school '
                                 'as entrance level')
        if self.enrollment_type.step_id != self.step_id:
            raise IntegrityError('Can\'t save SelectedEnrollmentType: '
                                 'Enrollment type should belong to the same step '
                                 'as this object')
        super().save(*args, **kwargs)
