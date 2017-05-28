import copy
import operator

import django.forms
import django.utils.timezone
import djchoices
import polymorphic.models
from cached_property import cached_property
from django.core import urlresolvers
from django.db import models

import frontend.forms
import schools.models
import sistema.models
import users.models
from sistema.helpers import group_by
from . import forms


class AbstractQuestionnaireBlock(polymorphic.models.PolymorphicModel):
    questionnaire = models.ForeignKey('Questionnaire',
                                      on_delete=models.CASCADE)

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    order = models.IntegerField(
        default=0,
        help_text='Блоки выстраиваются по возрастанию порядка')

    is_question = False

    def __str__(self):
        return '%s. %s' % (self.questionnaire, self.short_name)

    class Meta:
        verbose_name = 'questionnaire block'
        unique_together = [('short_name', 'questionnaire'),
                           ('questionnaire', 'order')]
        ordering = ('questionnaire_id', 'order')


class MarkdownQuestionnaireBlock(AbstractQuestionnaireBlock):
    block_name = 'markdown'

    markdown = models.TextField()

    def __str__(self):
        return self.markdown[:40]


class AbstractQuestionnaireQuestion(AbstractQuestionnaireBlock):
    is_question = True

    text = models.TextField(help_text='Вопрос')

    is_required = models.BooleanField(help_text='Является ли вопрос обязательным')

    help_text = models.CharField(max_length=400,
                                 blank=True,
                                 help_text='Подсказка, помогающая ответить на вопрос')

    is_disabled = models.BooleanField(default=False,
                                      help_text='Выключена ли возможность ответить на вопрос. Не может быть отмечено одновременно с is_required')

    def get_form_field(self, attrs=None):
        raise NotImplementedError('Child should implement its own method get_form_field()')

    def save(self, *args, **kwargs):
        if self.is_disabled and self.is_required:
            raise ValueError('questionnaire.AbstractQuestionnaireBlock: is_disabled can not be set with is_required')
        super().save(*args, **kwargs)

    def __str__(self):
        return '%s: %s' % (self.questionnaire, self.text)


class TextQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'text_question'

    is_multiline = models.BooleanField()

    placeholder = models.TextField(help_text='Подсказка, показываемая в поле для ввода; пример',
                                   blank=True)

    fa = models.CharField(max_length=20,
                          help_text='Имя иконки FontAwesome, которую нужно показать в поле',
                          blank=True)

    def get_form_field(self, attrs=None):
        if attrs is None:
            attrs = {}

        if 'placeholder' not in attrs:
            attrs['placeholder'] = self.placeholder

        if self.is_multiline:
            attrs['class'] = 'gui-textarea ' + attrs.pop('class', '')
        else:
            attrs['class'] = 'gui-input ' + attrs.pop('class', '')

        if self.fa != '':
            if 'fa' not in attrs:
                attrs['fa'] = self.fa
            if self.is_multiline:
                widget = frontend.forms.TextareaWithFaIcon(attrs)
            else:
                widget = frontend.forms.TextInputWithFaIcon(attrs)
        else:
            if self.is_multiline:
                widget = django.forms.Textarea(attrs)
            else:
                widget = django.forms.TextInput(attrs)

        return django.forms.CharField(
            required=self.is_required,
            disabled=self.is_disabled,
            help_text=self.help_text,
            label=self.text,
            widget=widget,
        )


class ChoiceQuestionnaireQuestionVariant(models.Model):
    text = models.TextField()

    question = models.ForeignKey('ChoiceQuestionnaireQuestion',
                                 on_delete=models.CASCADE,
                                 related_name='variants')

    order = models.PositiveIntegerField(default=0)

    # If variant is disabled it shows as gray and can't be selected
    is_disabled = models.BooleanField(default=False)

    # If this one is selected all options are disabled
    disable_question_if_chosen = models.BooleanField(default=False)

    def __str__(self):
        return '{}: {} {}'.format(self.question, self.id, self.text)


class ChoiceQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'choice_question'

    is_multiple = models.BooleanField()

    is_inline = models.BooleanField()

    def get_form_field(self, attrs=None):
        if attrs is None:
            attrs = {}

        choices = ((v.id, {'label': v.text, 'disabled': v.is_disabled})
                   for v in self.variants.order_by('order', 'id'))

        attrs['inline'] = self.is_inline
        if self.is_multiple:
            field_class = forms.TypedMultipleChoiceFieldForChoiceQuestion
            widget_class = frontend.forms.SistemaCheckboxSelect
        else:
            field_class = forms.TypedChoiceFieldForChoiceQuestion
            widget_class = frontend.forms.SistemaRadioSelect

        return field_class(
            question=self,
            required=self.is_required,
            disabled=self.is_disabled,
            coerce=int,
            choices=choices,
            widget=widget_class(attrs=attrs),
            label=self.text,
            help_text=self.help_text,
        )


class YesNoQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'yesno_question'

    def get_form_field(self, attrs=None):
        if attrs is None:
            attrs = {}

        return django.forms.TypedChoiceField(
            required=self.is_required,
            disabled=self.is_disabled,
            coerce=lambda x: x == 'True',
            choices=((False, 'Нет'), (True, 'Да')),
            widget=frontend.forms.SistemaRadioSelect(attrs=attrs),
            label=self.text,
            help_text=self.help_text,
        )


class DateQuestionnaireQuestion(AbstractQuestionnaireQuestion):
    block_name = 'date_question'

    with_year = models.BooleanField(default=True)

    min_year = models.PositiveIntegerField(null=True)

    max_year = models.PositiveIntegerField(null=True)

    def get_form_field(self, attrs=None):
        return django.forms.DateField(
            required=self.is_required,
            disabled=self.is_disabled,
            label=self.text,
            help_text=self.help_text,
            widget=django.forms.DateInput(attrs={
                'class': 'gui-input datetimepicker',
                'data-format': 'DD.MM.YYYY',
                'data-view-mode': 'years',
                'data-pick-time': 'false',
                'placeholder': 'дд.мм.гггг',
            }),
        )


class Questionnaire(models.Model):
    title = models.CharField(max_length=100, help_text='Название анкеты')

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием',
    )

    school = models.ForeignKey(schools.models.School, blank=True, null=True)

    session = models.ForeignKey(schools.models.Session, blank=True, null=True)

    close_time = models.DateTimeField(blank=True, null=True, default=None)

    enable_autofocus = models.BooleanField(
        default=True,
        help_text='Будет ли курсор автоматически фокусироваться на первом '
                  'вопросе при загрузке страницы',
    )

    should_record_typing_dynamics = models.BooleanField(default=False)

    def __str__(self):
        if self.school is not None:
            return '%s. %s' % (self.school, self.title)
        return self.title

    # TODO: Extract to ModelWithCloseTime?
    def is_closed(self):
        return self.close_time is not None and django.utils.timezone.now() >= self.close_time

    @cached_property
    def blocks(self):
        return sorted(self.abstractquestionnaireblock_set.all(), key=operator.attrgetter('order'))

    @cached_property
    def questions(self):
        questions = self.abstractquestionnaireblock_set.instance_of(AbstractQuestionnaireQuestion)
        return sorted(questions, key=operator.attrgetter('order'))

    @cached_property
    def show_conditions(self):
        return group_by(
            QuestionnaireBlockShowCondition.objects.filter(block__questionnaire=self),
            operator.attrgetter('block_id')
        )

    def get_form_class(self, attrs=None):
        if attrs is None:
            attrs = {}

        fields = {
            'prefix': self.get_prefix(),
        }

        is_first = True
        for question in self.questions:
            question_attrs = copy.copy(attrs)
            if is_first:
                if self.enable_autofocus:
                    question_attrs['autofocus'] = 'autofocus'
                is_first = False

            fields[question.short_name] = (
                question.get_form_field(question_attrs))

        form_class = type('%sForm' % self.short_name.title(),
                          (forms.QuestionnaireForm,),
                          fields)
        return form_class

    def get_prefix(self):
        return 'questionnaire_' + self.short_name

    def get_absolute_url(self):
        if self.school is None:
            return urlresolvers.reverse(
                'questionnaire',
                kwargs={'questionnaire_name': self.short_name},
            )
        else:
            return urlresolvers.reverse(
                'school:questionnaire',
                kwargs={'questionnaire_name': self.short_name,
                        'school_name': self.school.short_name}
            )

    def is_filled_by(self, user):
        user_status = self.statuses.filter(user=user).first()
        if user_status is None:
            return False

        return user_status.status == UserQuestionnaireStatus.Status.FILLED

    class Meta:
        unique_together = ('school', 'short_name')


class QuestionnaireAnswer(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, related_name='answers')

    user = models.ForeignKey(users.models.User,
                             related_name='questionnaire_answers')

    # TODO: may be ForeignKey is better?
    question_short_name = models.CharField(max_length=100)

    answer = models.TextField(blank=True)

    def __str__(self):
        return 'Ответ «%s» на вопрос %s анкеты %s' % (self.answer.replace('\n', '\\n'), self.question_short_name, self.questionnaire)

    @property
    def question(self):
        return AbstractQuestionnaireQuestion.objects.filter(questionnaire=self.questionnaire, short_name=self.question_short_name).first()

    class Meta:
        index_together = ('questionnaire', 'user', 'question_short_name')


# TODO: may be extract base class for this and modules.topics.models.UserQuestionnaireStatus?
class UserQuestionnaireStatus(models.Model):
    class Status(djchoices.DjangoChoices):
        NOT_FILLED = djchoices.ChoiceItem(1)
        FILLED = djchoices.ChoiceItem(2)

    user = models.ForeignKey(users.models.User, related_name='+')

    questionnaire = models.ForeignKey(Questionnaire, related_name='statuses')

    status = models.PositiveIntegerField(choices=Status.choices, validators=[Status.validator])

    class Meta:
        verbose_name_plural = 'User questionnaire statuses'
        unique_together = ('user', 'questionnaire')

    def __str__(self):
        return 'Status {} of {} for {}'.format(self.status, self.questionnaire, self.user)


class QuestionnaireBlockShowCondition(models.Model):
    # If there is at least one conditions for `block`,
    # it will be visible only if one `need_to_be_checked` is checked
    block = models.ForeignKey(AbstractQuestionnaireBlock, related_name='show_conditions')

    need_to_be_checked = models.ForeignKey(ChoiceQuestionnaireQuestionVariant, related_name='+')

    def __str__(self):
        return 'Show %s only if %s' % (self.block, self.need_to_be_checked)


# Used to evalute fraction of accounts where different persons filled
# questionnairies for students and parents. The estimation will be biased, but
# we will probably be able to measure changes in the next year comparing with
# the current one.
class QuestionnaireTypingDynamics(models.Model):
    user = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='+',
    )

    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='+',
    )

    typing_data = sistema.models.CompressedTextField(
        help_text='JSON с данными о нажатиях клавиш'
    )

    created_at = models.DateTimeField(auto_now_add=True)
