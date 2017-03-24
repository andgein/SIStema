from datetime import timedelta

from django import forms
from django.core import validators, urlresolvers
from django.db import models
from django.forms import widgets
import django.utils.timezone

import schools.models
import users.models
import modules.smartq.models as smartq_models

from djchoices import choices


class TopicQuestionnaire(models.Model):
    school = models.OneToOneField(schools.models.School)

    title = models.CharField(max_length=100)

    close_time = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self):
        return '%s. %s' % (self.school.name, self.title)

    def is_closed(self):
        return (self.close_time is not None and
                django.utils.timezone.now() >= self.close_time)

    def get_absolute_url(self):
        return urlresolvers.reverse(
            'school:topics:index',
            kwargs={'school_name': self.school.short_name})

    def get_status(self, user):
        qs = self.statuses.filter(user=user)
        if not qs.exists():
            return UserQuestionnaireStatus.Status.NOT_STARTED
        return qs.get().status

    def is_filled_by(self, user):
        return self.get_status(user) == UserQuestionnaireStatus.Status.FINISHED

    def get_filled_users_ids(self):
        return UserQuestionnaireStatus.objects.filter(
            questionnaire=self,
            status=UserQuestionnaireStatus.Status.FINISHED
        ).values_list('user_id', flat=True)


class TopicCheckingQuestionnaire(models.Model):
    class Status(choices.DjangoChoices):
        IN_PROGRESS = choices.ChoiceItem(1)
        REFUSED = choices.ChoiceItem(2)
        FAILED = choices.ChoiceItem(3)
        PASSED = choices.ChoiceItem(4)

    topic_questionnaire = models.ForeignKey(TopicQuestionnaire, related_name='+')

    user = models.ForeignKey(users.models.User, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)

    checked_at = models.DateTimeField(blank=True, null=True, default=None)

    status = models.PositiveIntegerField(choices=Status.choices, validators=[Status.validator])

    @classmethod
    def get_latest(cls, user, topic_questionnaire):
        try:
            smartq_q = cls.objects.filter(
                user=user, topic_questionnaire=topic_questionnaire).latest('created_at')
            return smartq_q
        except cls.DoesNotExist:
            return None

    def errors_count(self):
        err_count = 0
        for q in self.questions.all():
            # I was counting ok_counts, but artemtab made me think in negative way
            if q.checker_result != TopicCheckingQuestionnaireQuestion.CheckerResult.OK:
                err_count += 1
        return err_count

    def has_check_failed(self):
        for q in self.questions.all():
            if q.checker_result == TopicCheckingQuestionnaireQuestion.CheckerResult.CHECK_FAILED:
                return True
        return False

    def is_check_failed_expired(self):
        return django.utils.timezone.now() >= self.checked_at + timedelta(minutes=30)


class Level(models.Model):
    questionnaire = models.ForeignKey(TopicQuestionnaire)

    name = models.CharField(max_length=20)

    class Meta:
        unique_together = ('questionnaire', 'name')

    def __str__(self):
        return '%s. %s' % (self.questionnaire, self.name)


class LevelDependency(models.Model):
    questionnaire = models.ForeignKey(TopicQuestionnaire)

    source_level = models.ForeignKey(Level, related_name='+')

    destination_level = models.ForeignKey(Level, related_name='+')

    min_percent = models.IntegerField(
        help_text='Минимальный процент максимальных/минимальных оценок из '
                  'source_level',
        validators=[validators.MinValueValidator(
                        0, message='Процент не может быть меньше нуля'),
                    validators.MaxValueValidator(
                        100, message='Процент не может быть больше 100')]
    )

    def __str__(self):
        return '%s. Downward %s → %s (%d%%)' % (self.questionnaire,
                                                self.source_level.name,
                                                self.destination_level.name,
                                                self.min_percent)

    def save(self, *args, **kwargs):
        q1 = self.source_level.questionnaire
        q2 = self.destination_level.questionnaire
        if q1 != q2 or q2 != self.questionnaire:
            raise ValueError(
                'topics.settings.LevelDependency: source_level and '
                'destination_level should be set up as one of questionnaire '
                'level')

        super(LevelDependency, self).save(*args, **kwargs)

    def satisfy(self, marks_count, total_questions):
        """
        :return: marks_count / total_questions >= self.min_percent%
        """
        return marks_count * 100 >= total_questions * self.min_percent

    class Meta:
        abstract = True
        unique_together = ('source_level', 'destination_level')


class LevelDownwardDependency(LevelDependency):
    """
    Если школьник знает на максимальный балл хотя бы min_percent процентов тем
    из source_level, то он также знает все темы из destination_level.
    """

    class Meta:
        verbose_name_plural = 'Level downward dependencies'


class LevelUpwardDependency(LevelDependency):
    """
    Если школьник знает на минимальный балл хотя бы min_percent процентов тем из
    source_level, то он не знает ни одной темы из destination_level.
    """

    class Meta:
        verbose_name_plural = 'Level upward dependencies'


class Scale(models.Model):
    questionnaire = models.ForeignKey(TopicQuestionnaire)

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    title = models.CharField(
        max_length=100,
        help_text='Например, «Практика». Показывается школьнику')

    count_values = models.PositiveIntegerField()

    class Meta:
        unique_together = ('questionnaire', 'short_name')

    def get_label_group(self, group_name):
        labels = ScaleLabel.objects.where(group__short_name=group_name)
        if labels.count() != self.count_values:
            raise AssertionError(
                'topics.models.Scale.get_label_group: labels count in group '
                '"%s" (%d) must be equal to count_values defined in scale (%d)'
                % (group_name, labels.count(), self.count_values))

        return [l.label_text for l in labels]

    def __str__(self):
        return '%s. Шкала %s' % (self.questionnaire, self.title)

    @property
    def max_mark(self):
        return self.count_values - 1


class ScaleLabelGroup(models.Model):
    scale = models.ForeignKey(Scale, related_name='label_groups')

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    def __str__(self):
        return '%s, группа %s' % (self.scale, self.short_name)

    class Meta:
        unique_together = ('scale', 'short_name')


class ScaleLabel(models.Model):
    group = models.ForeignKey(ScaleLabelGroup, related_name='labels')

    mark = models.PositiveIntegerField()

    label_text = models.TextField()

    def __str__(self):
        return '%s. Вариант «%s»' % (self.group, self.label_text)


class Tag(models.Model):
    questionnaire = models.ForeignKey(TopicQuestionnaire)

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    title = models.CharField(max_length=100)

    def __str__(self):
        return '%s. Тег «%s»' % (self.questionnaire, self.title)

    class Meta:
        unique_together = ('questionnaire', 'short_name')


class Topic(models.Model):
    questionnaire = models.ForeignKey(TopicQuestionnaire)

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    title = models.CharField(
        max_length=100,
        help_text='Показывается школьнику при заполнении анкеты')

    text = models.TextField(
        help_text='Более подробное описание. Показывается школьнику при '
                  'заполнении анкеты')

    level = models.ForeignKey(Level)

    tags = models.ManyToManyField(Tag, blank=True, related_name='topics')

    order = models.IntegerField(
        default=0,
        help_text='Внутренний порядок возрастания сложности')

    class Meta:
        unique_together = ('questionnaire', 'short_name')

    def save(self, *args, **kwargs):
        # TODO: check all tags too
        if self.level.questionnaire == self.questionnaire:
            super(Topic, self).save(*args, **kwargs)
        else:
            raise ValueError('topics.settings.Topic: level must be set up as '
                             'one of questionnaire level')

    def __str__(self):
        return '%s. Тема «%s»' % (self.questionnaire, self.title)

    def get_form_class(self, scales_issues):
        fields = {'topic_id': forms.IntegerField(widget=widgets.HiddenInput(),
                                                 initial=self.id)}

        # TODO: optimize database queries
        for idx, scale_issue in enumerate(scales_issues):
            scale = ScaleInTopic.objects.filter(
                topic=self,
                scale_label_group=scale_issue.label_group).get()
            scale_label_group = scale.scale_label_group
            labels = ScaleLabel.objects.filter(group=scale_label_group)
            name = '%s__%s__%s' % (self.short_name,
                                   scale_label_group.scale.short_name,
                                   scale_label_group.short_name)

            # TODO: extract to class
            fields[name] = forms.TypedChoiceField(
                label=scale.scale.title,
                choices=[(label.mark, label.label_text) for label in labels],
                coerce=int,
                required=True,
                error_messages={
                    'required': 'Выберите вариант',
                    'invalid_choice': 'Какой-то неправильный вариант. Давайте '
                                      'попробуем ещё раз'},
                widget=widgets.RadioSelect(attrs={}))

        return type('%sForm' % self.short_name, (forms.Form,), fields)


class ScaleInTopic(models.Model):
    topic = models.ForeignKey(Topic)

    scale_label_group = models.ForeignKey(ScaleLabelGroup)

    @property
    def scale(self):
        return self.scale_label_group.scale

    @property
    def questionnaire(self):
        return self.topic.questionnaire

    def __str__(self):
        return '.'.join([self.topic.questionnaire.school.short_name,
                         self.topic.short_name,
                         self.scale.short_name])

    class Meta:
        unique_together = ('topic', 'scale_label_group')


class TopicDependency(models.Model):
    """
    Каждая зависимость описана в виде кортежа (src_entry, src_scale, dst_entry,
    dst_scale, function), и говорит, что шкала dst_scale темы dst_entry зависит
    от шкалы src_scale темы src_entry как function.

    Проще говоря, если знаешь src, то знаешь dst.

    Если function равен {0: [0, 1, 2], 1: [1, 2], 2: [2]}, то это значит, что:
    При значении src_scale = 0, dst_scale может принимать значения 0, 1, 2.
    При значении src_scale = 1, dst_scale может принимать значения 1, 2.
    При значении src_scale = 2, dst_scale может быть равно только 2.

    Все указанные в конфигах зависимости от более сложных тем к более простым.
    Поэтому вместе с каждой зависимостью надо добавлять обратную ей (получается
    инверсией отображения).
    """
    source = models.ForeignKey(ScaleInTopic,
                               related_name='dependencies_as_source_topic')

    destination = models.ForeignKey(
        ScaleInTopic,
        related_name='dependencies_as_destination_topic')

    source_mark = models.PositiveIntegerField()

    destination_mark = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.source.questionnaire == self.destination.questionnaire:
            super(TopicDependency, self).save(*args, **kwargs)
        else:
            raise ValueError('topics.settings.TopicDependency: source and '
                             'destination should be from one questionnaire')

    def __str__(self):
        return 'Зависимость от «%s» (оценка %d) к «%s» (оценка %d)' % (
            self.source, self.source_mark, self.destination,
            self.destination_mark)

    class Meta:
        index_together = (('source', 'destination'), ('source', 'source_mark'))
        verbose_name_plural = 'Topic dependencies'


class UserQuestionnaireStatus(models.Model):
    class Status(choices.DjangoChoices):
        NOT_STARTED = choices.ChoiceItem(1)
        STARTED = choices.ChoiceItem(2)
        CORRECTING = choices.ChoiceItem(3)
        FINISHED = choices.ChoiceItem(4)
        CHECK_TOPICS = choices.ChoiceItem(5)

    user = models.ForeignKey(users.models.User, related_name='+')

    questionnaire = models.ForeignKey(TopicQuestionnaire,
                                      related_name='statuses')

    status = models.PositiveIntegerField(choices=Status.choices,
                                         validators=[Status.validator])

    def __str__(self):
        return 'Пользователь %s. %s. Статус: %s' % (self.user,
                                                    self.questionnaire,
                                                    self.status)

    class Meta:
        verbose_name_plural = 'User questionnaire statuses'
        unique_together = ('user', 'questionnaire')


class BaseMark(models.Model):
    user = models.ForeignKey(users.models.User)

    scale_in_topic = models.ForeignKey(ScaleInTopic)

    mark = models.PositiveIntegerField()

    is_automatically = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.mark > self.scale_in_topic.scale.count_values:
            raise Exception('topics.models.UserMark: mark can\'t be greater '
                            'than scale\'s count_values')
        super(BaseMark, self).save(*args, **kwargs)

    def __str__(self):
        return 'Оценка %d пользователя %s за «%s» %s' % (
            self.mark, self.user, self.scale_in_topic,
            ' (автоматически)' if self.is_automatically else '')

    class Meta:
        unique_together = ('user', 'scale_in_topic')
        abstract = True


class UserMark(BaseMark):
    pass


class BackupUserMark(BaseMark):
    def __str__(self):
        return (super(BackupUserMark, self).__str__() +
                ' [оценка была исправлена]')


class TopicIssue(models.Model):
    user = models.ForeignKey(users.models.User)

    topic = models.ForeignKey(Topic)

    created_at = models.DateTimeField(auto_now_add=True)

    is_correcting = models.BooleanField(default=False)

    def __str__(self):
        return '%s (%s) выдана пользователю %s в %s' % (
            self.topic,
            ', '.join(str(s.label_group) for s in self.scales.all()),
            self.user,
            self.created_at)


class ScaleInTopicIssue(models.Model):
    topic_issue = models.ForeignKey(TopicIssue, related_name='scales')

    # TODO: may be store scale_in_topic, not label_group?
    label_group = models.ForeignKey(ScaleLabelGroup)


class QuestionForTopic(models.Model):
    scale_in_topic = models.ForeignKey(ScaleInTopic,
            related_name='smartq_mapping',
            help_text='Question is for this topic')

    mark = models.PositiveIntegerField(
        help_text='Question will be asked is this mark is equal to user mark '
                  'for topic')

    smartq_question = models.ForeignKey(
        smartq_models.Question,
        related_name='topic_mapping',
        help_text='Base checking question without specified numbers')

    group = models.IntegerField(
        blank=True, null=True, default=None,
        help_text='Same group indicates similar questions, e.g. bfs/dfs, and '
                  'only one of them is asked')

    def __str__(self):
        return '{} -> {}'.format((self.scale_in_topic, self.mark),
                                 self.smartq_question)


class TopicCheckingSettings(models.Model):
    questionnaire = models.ForeignKey(TopicQuestionnaire)

    max_questions = models.PositiveIntegerField()
 
    @property
    def allowed_errors_map(self):
        # TODO: not hardcode
        return {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 2}


class TopicCheckingQuestionnaireQuestion(models.Model):
    # Modify together with smartq
    class CheckerResult(choices.DjangoChoices):
        # TODO: no doubling the Checker result from smartq
        OK = choices.ChoiceItem(1)
        WRONG_ANSWER = choices.ChoiceItem(2)
        PRESENTATION_ERROR = choices.ChoiceItem(3)
        CHECK_FAILED = choices.ChoiceItem(4)

    questionnaire = models.ForeignKey(TopicCheckingQuestionnaire,
                                      related_name='questions')

    generated_question = models.ForeignKey(smartq_models.GeneratedQuestion,
                                           related_name='+')

    topic_mapping = models.ForeignKey(QuestionForTopic, related_name='+')

    checker_result = models.PositiveIntegerField(
        choices=CheckerResult.choices,
        validators=[CheckerResult.validator],
        blank=True,
        null=True,
        default=None)

    checker_message = models.CharField(
        max_length=2000, blank=True, null=True, default=None)

