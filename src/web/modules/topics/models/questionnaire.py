import collections
import operator

import django.utils.timezone
from django import forms
from django.apps import apps
from django.conf import settings
from django.core import validators
from django.db import models, transaction, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import widgets
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djchoices import choices

import modules.entrance.levels as entrance_levels
import modules.entrance.models as entrance_models
import schools.models
import sistema.helpers


class TopicQuestionnaire(models.Model):
    school = models.OneToOneField(
        schools.models.School,
        on_delete=models.CASCADE,
    )

    title = models.CharField(max_length=100)

    close_time = models.DateTimeField(blank=True, null=True, default=None)

    previous = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Её оценки используются для автоматического заполнения этой '
                  'ТА',
    )

    def __str__(self):
        return '%s. %s' % (self.school.name, self.title)

    def is_closed(self):
        return (self.close_time is not None and
                django.utils.timezone.now() >= self.close_time)

    def get_absolute_url(self):
        return reverse(
            'school:topics:index',
            kwargs={'school_name': self.school.short_name})

    def get_status(self, user):
        qs = self.statuses.filter(user=user)
        if not qs.exists():
            return UserQuestionnaireStatus.Status.NOT_STARTED
        return qs.get().status

    def is_filled_by(self, user):
        return self.get_status(user) == UserQuestionnaireStatus.Status.FINISHED

    def get_filled_user_ids(self):
        return UserQuestionnaireStatus.objects.filter(
            questionnaire=self,
            status=UserQuestionnaireStatus.Status.FINISHED
        ).values_list('user_id', flat=True)

    KEEP_VALUE = object()

    @transaction.atomic
    def clone(self,
              *,
              school,
              title=KEEP_VALUE,
              close_time=KEEP_VALUE,
              previous=None):
        """
        Make and return a full copy of the topics questionnaire.

        :param school: A school to clone the questionnaire to.
        :param title: Title for the new questionnaire. Not changed by default.
        :param close_time: Close time for the new questionnaire. Not changed
            by default.
        :param previous: Previous questionnaire for the new questionnaire. Set
            to None by default.
        :return: The fresh copy of a questionnaire.
        """
        if self.pk is None:
            raise ValueError(
                "The questionnaire should be in database to be cloned")

        if title is self.KEEP_VALUE:
            title = self.title
        if close_time is self.KEEP_VALUE:
            close_time = self.close_time

        new_questionnaire = TopicQuestionnaire.objects.create(
            school=school,
            title=title,
            close_time=close_time,
            previous=previous,
        )

        self._copy_levels_with_deps_to_questionnaire(new_questionnaire)
        self._copy_tags_to_questionnaire(new_questionnaire)
        self._copy_topics_to_questionnaire(new_questionnaire)
        self._copy_scales_with_labels_to_questionnaire(new_questionnaire)
        self._copy_scales_in_topics_to_questionnaire(new_questionnaire)
        self._copy_topic_deps_to_questionnaire(new_questionnaire)
        self._copy_checking_settings_to_questionnaire(new_questionnaire)
        self._copy_checking_questions_to_questionnaire(new_questionnaire)

        return new_questionnaire

    def _copy_levels_with_deps_to_questionnaire(self, to_questionnaire):
        for level in self.levels.all():
            level.copy_to_questionnaire(to_questionnaire)

        for dep in LevelUpwardDependency.objects.filter(questionnaire=self):
            dep.copy_to_questionnaire(to_questionnaire)

        for dep in LevelDownwardDependency.objects.filter(questionnaire=self):
            dep.copy_to_questionnaire(to_questionnaire)

    def _copy_tags_to_questionnaire(self, to_questionnaire):
        for tag in self.tags.all():
            tag.copy_to_questionnaire(to_questionnaire)

    def _copy_topics_to_questionnaire(self, to_questionnaire):
        for topic in self.topics.all():
            topic.copy_to_questionnaire(to_questionnaire)

    def _copy_scales_with_labels_to_questionnaire(self, to_questionnaire):
        for scale in self.scales.all():
            scale.copy_to_questionnaire(to_questionnaire)

    def _copy_scales_in_topics_to_questionnaire(self, to_questionnaire):
        scale_in_topics = ScaleInTopic.objects.filter(topic__questionnaire=self)
        for scale_in_topic in scale_in_topics:
            scale_in_topic.copy_to_questionnaire(to_questionnaire)

    def _copy_topic_deps_to_questionnaire(self, to_questionnaire):
        src_deps = (
            TopicDependency.objects
            .filter(source__topic__questionnaire=self))
        for dep in src_deps:
            dep.copy_to_questionnaire(to_questionnaire)

    def _copy_checking_settings_to_questionnaire(self, to_questionnaire):
        checking_settings = (
            apps.get_model('topics', 'TopicCheckingSettings').objects
            .filter(questionnaire=self))
        for s in checking_settings:
            s.copy_to_questionnaire(to_questionnaire)

    def _copy_checking_questions_to_questionnaire(self, to_questionnaire):
        checking_question_for_topics = (
            apps.get_model('topics', 'QuestionForTopic').objects
            .filter(scale_in_topic__topic__questionnaire=self)
        )
        for q in checking_question_for_topics:
            q.copy_to_questionnaire(to_questionnaire)


class Level(models.Model):
    questionnaire = models.ForeignKey(
        TopicQuestionnaire,
        on_delete=models.CASCADE,
        related_name='levels',
    )

    name = models.CharField(max_length=20)

    class Meta:
        unique_together = ('questionnaire', 'name')

    def __str__(self):
        return '%s. %s' % (self.questionnaire, self.name)

    def copy_to_questionnaire(self, to_questionnaire):
        return self.__class__.objects.create(
            questionnaire=to_questionnaire,
            name=self.name,
        )

    def get_clone_in_questionnaire(self, questionnaire):
        return questionnaire.levels.get(name=self.name)


class LevelDependency(models.Model):
    questionnaire = models.ForeignKey(
        TopicQuestionnaire,
        on_delete=models.CASCADE,
    )

    source_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='+',
    )

    destination_level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='+',
    )

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
            raise IntegrityError(
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

    def copy_to_questionnaire(self, to_questionnaire):
        src = self.source_level.get_clone_in_questionnaire(to_questionnaire)
        dst = self.destination_level.get_clone_in_questionnaire(
            to_questionnaire,
        )
        return self.__class__.objects.create(
            questionnaire=to_questionnaire,
            source_level=src,
            destination_level=dst,
            min_percent=self.min_percent,
        )


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
    questionnaire = models.ForeignKey(
        TopicQuestionnaire,
        on_delete=models.CASCADE,
        related_name='scales',
    )

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

    def copy_to_questionnaire(self, to_questionnaire):
        new_scale = self.__class__.objects.create(
            questionnaire=to_questionnaire,
            short_name=self.short_name,
            title=self.title,
            count_values=self.count_values,
        )

        for label_group in self.label_groups.all():
            label_group.copy_to_questionnaire(to_questionnaire)

        return new_scale

    def get_clone_in_questionnaire(self, questionnaire):
        return questionnaire.scales.get(short_name=self.short_name)


class ScaleLabelGroup(models.Model):
    scale = models.ForeignKey(
        Scale,
        on_delete=models.CASCADE,
        related_name='label_groups',
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    def __str__(self):
        return '%s, группа %s' % (self.scale, self.short_name)

    class Meta:
        unique_together = ('scale', 'short_name')

    def copy_to_questionnaire(self, to_questionnaire):
        dst_scale = self.scale.get_clone_in_questionnaire(to_questionnaire)
        new_label_group = self.__class__.objects.create(
            scale=dst_scale,
            short_name=self.short_name,
        )
        for label in self.labels.all():
            label.pk = None
            label.group = new_label_group
            label.save()
        return new_label_group

    def get_clone_in_questionnaire(self, questionnaire):
        scale_clone = self.scale.get_clone_in_questionnaire(questionnaire)
        return self.__class__.objects.get(
            scale=scale_clone,
            short_name=self.short_name,
        )


class ScaleLabel(models.Model):
    group = models.ForeignKey(
        ScaleLabelGroup,
        on_delete=models.CASCADE,
        related_name='labels',
    )

    mark = models.PositiveIntegerField()

    label_text = models.TextField()

    def __str__(self):
        return '%s. Вариант «%s»' % (self.group, self.label_text)


class Tag(models.Model):
    questionnaire = models.ForeignKey(
        TopicQuestionnaire,
        on_delete=models.CASCADE,
        related_name='tags',
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием')

    title = models.CharField(max_length=100)

    def __str__(self):
        return '%s. Тег «%s»' % (self.questionnaire, self.title)

    class Meta:
        unique_together = ('questionnaire', 'short_name')

    def copy_to_questionnaire(self, to_questionnaire):
        return self.__class__.objects.create(
            questionnaire=to_questionnaire,
            short_name=self.short_name,
            title=self.title,
        )


class Topic(models.Model):
    questionnaire = models.ForeignKey(
        TopicQuestionnaire,
        on_delete=models.CASCADE,
        related_name='topics',
    )

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

    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
    )

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
            raise IntegrityError(
                'topics.settings.Topic: level must be set up as '
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

    def copy_to_questionnaire(self, to_questionnaire):
        new_topic = self.__class__.objects.create(
            questionnaire=to_questionnaire,
            short_name=self.short_name,
            title=self.title,
            text=self.text,
            level=self.level.get_clone_in_questionnaire(to_questionnaire),
            order=self.order,
        )
        for tag in self.tags.all():
            dst_tag = to_questionnaire.tags.get(short_name=tag.short_name)
            new_topic.tags.add(dst_tag)
        return new_topic

    def get_clone_in_questionnaire(self, questionnaire):
        return questionnaire.topics.get(short_name=self.short_name)


class ScaleInTopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    scale_label_group = models.ForeignKey(
        ScaleLabelGroup,
        on_delete=models.CASCADE,
    )

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

    def copy_to_questionnaire(self, to_questionnaire):
        dst_topic = self.topic.get_clone_in_questionnaire(to_questionnaire)
        dst_scale_label_group = (
            self.scale_label_group.get_clone_in_questionnaire(to_questionnaire))
        return self.__class__.objects.create(
            topic=dst_topic,
            scale_label_group=dst_scale_label_group,
        )

    def get_clone_in_questionnaire(self, questionnaire):
        return self.__class__.objects.get(
            topic=self.topic.get_clone_in_questionnaire(questionnaire),
            scale_label_group=self.scale_label_group.get_clone_in_questionnaire(
                questionnaire)
        )


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
    source = models.ForeignKey(
        ScaleInTopic,
        on_delete=models.CASCADE,
        related_name='dependencies_as_source_topic',
    )

    destination = models.ForeignKey(
        ScaleInTopic,
        on_delete=models.CASCADE,
        related_name='dependencies_as_destination_topic',
    )

    source_mark = models.PositiveIntegerField()

    destination_mark = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.source.questionnaire.id != self.destination.questionnaire.id:
            raise IntegrityError(
                'topics.settings.TopicDependency: source and '
                'destination should be from one questionnaire'
            )
        super(TopicDependency, self).save(*args, **kwargs)

    def __str__(self):
        return 'Зависимость от «%s» (оценка %d) к «%s» (оценка %d)' % (
            self.source, self.source_mark, self.destination,
            self.destination_mark)

    class Meta:
        index_together = (('source', 'destination'), ('source', 'source_mark'))
        verbose_name_plural = 'Topic dependencies'

    def copy_to_questionnaire(self, to_questionnaire):
        return self.__class__.objects.create(
            source=self.source.get_clone_in_questionnaire(to_questionnaire),
            destination=self.destination.get_clone_in_questionnaire(
                to_questionnaire),
            source_mark=self.source_mark,
            destination_mark=self.destination_mark,
        )


class UserQuestionnaireStatus(models.Model):
    class Status(choices.DjangoChoices):
        NOT_STARTED = choices.ChoiceItem(1)
        STARTED = choices.ChoiceItem(2)
        CORRECTING = choices.ChoiceItem(3)
        FINISHED = choices.ChoiceItem(4)
        CHECK_TOPICS = choices.ChoiceItem(5)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )

    questionnaire = models.ForeignKey(
        'TopicQuestionnaire',
        on_delete=models.CASCADE,
        related_name='statuses',
    )

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    scale_in_topic = models.ForeignKey('ScaleInTopic', on_delete=models.CASCADE)

    mark = models.PositiveIntegerField()

    is_automatically = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.mark > self.scale_in_topic.scale.count_values:
            raise Exception('topics.models.UserMark: mark can\'t be greater '
                            'than scale\'s count_values')
        super(BaseMark, self).save(*args, **kwargs)

    def __str__(self):
        return 'Оценка %d пользователя %s за «%s» %s%s' % (
            self.mark, self.user, self.scale_in_topic, self.created_at,
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    topic = models.ForeignKey('Topic', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    is_correcting = models.BooleanField(default=False)

    def __str__(self):
        return '%s (%s) выдана пользователю %s в %s' % (
            self.topic,
            ', '.join(str(s.label_group) for s in self.scales.all()),
            self.user,
            self.created_at)


class ScaleInTopicIssue(models.Model):
    topic_issue = models.ForeignKey(
        TopicIssue,
        on_delete=models.CASCADE,
        related_name='scales',
    )

    # TODO: may be store scale_in_topic, not label_group?
    label_group = models.ForeignKey('ScaleLabelGroup', on_delete=models.CASCADE)


class EntranceLevelRequirement(models.Model):
    """
    Каждое требование задаётся кортежом (tag, max_penalty).
    Это значит, что сумма баллов школьника по всем шкалам всех тем с тегом tag
    должна отличаться от максимальной не более чем на max_penalty.
    """
    questionnaire = models.ForeignKey(
        'topics.TopicQuestionnaire',
        on_delete=models.CASCADE,
    )

    # TODO(artemtab): make it independent from the entrance module
    entrance_level = models.ForeignKey(
        'entrance.EntranceLevel',
        on_delete=models.CASCADE,
    )

    tag = models.ForeignKey(
        'topics.Tag',
        on_delete=models.CASCADE,
    )

    max_penalty = models.PositiveIntegerField()

    class Meta:
        unique_together = ('questionnaire', 'entrance_level', 'tag')

    def __str__(self):
        return 'EntranceLevelRequirement(level: {}, tag: {}, max_penalty: {})'.format(
                    self.entrance_level.name, self.tag.title, self.max_penalty)

    def satisfy(self, sum_marks, max_marks):
        return max_marks - sum_marks <= self.max_penalty


class TopicsEntranceLevelLimit(models.Model):
    """
    This model is used to cache entrance level inferred from the topics
    questionnaire.
    """
    questionnaire = models.ForeignKey(
        'TopicQuestionnaire',
        on_delete=models.CASCADE,
        verbose_name='тематическая анкета',
        related_name='cached_level_limits',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='пользователь',
        related_name='+',
    )

    level = models.ForeignKey(
        'entrance.EntranceLevel',
        on_delete=models.CASCADE,
        verbose_name='уровень',
        related_name='+',
    )

    class Meta:
        verbose_name = _('topics entrance level limit')
        verbose_name_plural = _('topics entrance level limits')
        unique_together = ('questionnaire', 'user')

    def __str__(self):
        return '{} для {} в {}'.format(
            self.level, self.user, self.questionnaire)

    @classmethod
    def get_limit(cls, *, user, questionnaire):
        cached_limit = (
            cls.objects
            .filter(user=user, questionnaire=questionnaire)
            .select_related('level')
            .first())
        if cached_limit is None:
            level = cls._compute_level(user=user, questionnaire=questionnaire)
            cached_limit = cls.objects.create(
                user=user, questionnaire=questionnaire, level=level)
        return entrance_levels.EntranceLevelLimit(cached_limit.level)

    @classmethod
    def _compute_level(cls, *, user, questionnaire):
        # TODO: don't put a limit if questionnaire status is not FINISHED

        user_marks = (
            UserMark.objects
            .filter(user=user,
                    scale_in_topic__topic__questionnaire=questionnaire)
            .prefetch_related('scale_in_topic__topic__tags'))

        requirements = (
            EntranceLevelRequirement.objects
            .filter(questionnaire=questionnaire)
            .prefetch_related('entrance_level'))
        requirements_by_tag = sistema.helpers.group_by(
            requirements, operator.attrgetter('tag_id'))
        requirements_by_level = sistema.helpers.group_by(
            requirements, operator.attrgetter('entrance_level'))
        sum_marks_for_requirements = collections.defaultdict(int)
        max_marks_for_requirements = collections.defaultdict(int)

        for mark in user_marks:
            scale_in_topic = mark.scale_in_topic
            topic = scale_in_topic.topic
            topic_tags = topic.tags.all()

            for tag in topic_tags:
                for requirement in requirements_by_tag[tag.id]:
                    sum_marks_for_requirements[requirement.id] += mark.mark
                    max_marks_for_requirements[requirement.id] += (
                        scale_in_topic.scale.max_mark)

        # Если всё плохо, самый просто уровень считаем выполненным — иначе
        # нечего будет решать
        maximum_satisfied_level = (
            entrance_models.EntranceLevel.objects
            .filter(school=questionnaire.school)
            .order_by('order').first())
        for level, requirements_for_level in requirements_by_level.items():
            all_satisfied = True
            for requirement in requirements_for_level:
                all_satisfied = all_satisfied and requirement.satisfy(
                    sum_marks_for_requirements[requirement.id],
                    max_marks_for_requirements[requirement.id],
                )

            if all_satisfied:
                if level.order > maximum_satisfied_level.order:
                    maximum_satisfied_level = level

        return maximum_satisfied_level


@receiver(post_save, sender=UserQuestionnaireStatus)
def clear_entrance_level_cache(sender, instance, **kwargs):
    TopicsEntranceLevelLimit.objects.filter(
        user=instance.user,
        questionnaire=instance.questionnaire,
    ).delete()
