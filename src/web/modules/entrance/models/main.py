import datetime

import re

import djchoices
import polymorphic.models
from django.core import urlresolvers
from django.conf import settings
from django.db import models, transaction
import django.utils.timezone

import schools.models
import modules.ejudge.models
import users.models


class EntranceExamTask(models.Model):
    title = models.CharField(max_length=100, help_text='Название')

    text = models.TextField(help_text='Формулировка задания')

    exam = models.ForeignKey('EntranceExam', related_name='%(class)s')

    help_text = models.CharField(max_length=100,
                                 help_text='Дополнительная информация, например, сведения о формате ответа',
                                 blank=True)

    max_score = models.PositiveIntegerField()

    def __str__(self):
        return self.title

    def get_child_object(self):
        child = [TestEntranceExamTask, FileEntranceExamTask, ProgramEntranceExamTask]
        for children in child:
            class_name = children.__name__.lower()
            if hasattr(self, class_name):
                return getattr(self, class_name)

        return None

    def is_solved_by_user(self, user):
        # Always not solved by default. Override when subclassing.
        return False


class TestEntranceExamTask(EntranceExamTask):
    correct_answer_re = models.CharField(max_length=100, help_text='Правильный ответ (регулярное выражение)')

    validation_re = models.CharField(max_length=100,
                                     help_text='Регулярное выражение для валидации ввода',
                                     blank=True)

    def check_solution(self, solution):
        return re.fullmatch(self.correct_answer_re, solution) is not None


class FileEntranceExamTask(EntranceExamTask):
    pass


class ProgramEntranceExamTask(EntranceExamTask):
    ejudge_contest_id = models.PositiveIntegerField(help_text='ID контеста в еджадже')

    ejudge_problem_id = models.PositiveIntegerField(help_text='ID задачи в еджадже')

    input_file_name = models.CharField(max_length=100, blank=True)

    output_file_name = models.CharField(max_length=100, blank=True)

    time_limit = models.PositiveIntegerField()

    memory_limit = models.PositiveIntegerField()

    input_format = models.TextField(blank=True)

    output_format = models.TextField(blank=True)

    def is_solved_by_user(self, user):
        related_field = 'programentranceexamtasksolution__ejudge_queue_element__submission__result'
        user_solutions = [s.programentranceexamtasksolution
                          for s in self.entranceexamtasksolution_set.filter(user=user)
                                       .select_related(related_field)]
        task_has_ok = any(filter(lambda s: s.is_checked and s.result.is_success, user_solutions))
        return task_has_ok


class EntranceExam(models.Model):
    school = models.OneToOneField(schools.models.School)

    close_time = models.DateTimeField(blank=True, default=None, null=True)

    def __str__(self):
        return 'Вступительная работа для %s' % self.school

    def is_closed(self):
        return self.close_time is not None and django.utils.timezone.now() >= self.close_time

    def get_absolute_url(self):
        return urlresolvers.reverse('school:entrance:exam', kwargs={ 'school_name': self.school.short_name})


class EntranceStep(models.Model):
    school = models.ForeignKey(schools.models.School, related_name='entrance_steps')

    class_name = models.CharField(max_length=100, help_text='Путь до класса, описывающий шаг')

    params = models.TextField(help_text='Параметры для шага')

    order = models.IntegerField()

    def __str__(self):
        return 'Шаг %s используется для %s' % (self.class_name, self.school)

    class Meta:
        ordering = ['order']


class EntranceLevel(models.Model):
    """
    Уровень вступительной работы.
    Для каждой задачи могут быть указаны уровни, для которых она предназначена.
    Уровень школьника определяется с помощью EntranceLevelLimiter'ов (например, на основе тематической анкеты
    из модуля topics или прошлой учёбы в других параллелях)
    """
    school = models.ForeignKey(schools.models.School)

    short_name = models.CharField(max_length=100,
                                  help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')

    name = models.CharField(max_length=100)

    order = models.IntegerField(default=0)

    tasks = models.ManyToManyField(EntranceExamTask, blank=True)

    def __str__(self):
        return 'Уровень «%s» для %s' % (self.name, self.school)

    def __gt__(self, other):
        return self.order > other.order

    def __lt__(self, other):
        return self.order < other.order

    def __ge__(self, other):
        return self.order >= other.order

    def __le__(self, other):
        return self.order <= other.order

    class Meta:
        ordering = ('school_id', 'order')


class EntranceExamTaskSolution(models.Model):
    task = models.ForeignKey(EntranceExamTask)

    user = models.ForeignKey(users.models.User)

    solution = models.TextField()

    ip = models.CharField(max_length=50,
                          help_text='IP-адрес, с которого было отправлено решение',
                          default='')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Решение %s по задаче %s' % (self.user, self.task)

    class Meta:
        ordering = ['-created_at']

        index_together = ('task', 'user')


class FileEntranceExamTaskSolution(EntranceExamTaskSolution):
    original_filename = models.TextField()


class ProgramEntranceExamTaskSolution(EntranceExamTaskSolution):
    language = models.ForeignKey(modules.ejudge.models.ProgrammingLanguage)

    ejudge_queue_element = models.ForeignKey(modules.ejudge.models.QueueElement)

    @property
    def is_checked(self):
        return self.ejudge_queue_element.status == modules.ejudge.models.QueueElement.Status.CHECKED

    @property
    def result(self):
        if not self.is_checked:
            return None
        return self.ejudge_queue_element.get_result()


class EntranceLevelUpgrade(models.Model):
    user = models.ForeignKey(users.models.User)

    upgraded_to = models.ForeignKey(EntranceLevel, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)


class EntranceLevelUpgradeRequirement(models.Model):
    base_level = models.ForeignKey(EntranceLevel, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)

    def get_child_object(self):
        child = [SolveTaskEntranceLevelUpgradeRequirement]
        for children in child:
            class_name = children.__name__.lower()
            if hasattr(self, class_name):
                return getattr(self, class_name)

        return None

    def is_met_by_user(self, user):
        # Always met by default. Override when subclassing.
        return True


class SolveTaskEntranceLevelUpgradeRequirement(EntranceLevelUpgradeRequirement):
    task = models.ForeignKey(EntranceExamTask, related_name='+')

    def is_met_by_user(self, user):
        return self.task.get_child_object().is_solved_by_user(user)


class CheckingGroup(models.Model):
    school = models.ForeignKey(schools.models.School)

    short_name = models.CharField(max_length=100,
                                  help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')

    name = models.CharField(max_length=100)

    def __str__(self):
        return 'Группа проверки %s для %s' % (self.name, self.school)

    class Meta:
        unique_together = ('school', 'short_name')


class UserInCheckingGroup(models.Model):
    user = models.ForeignKey(users.models.User)

    group = models.ForeignKey(CheckingGroup)

    is_actual = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s: пользователь %s' % (self.group, self.user)

    class Meta:
        ordering = ('-created_at', )

    @classmethod
    @transaction.atomic
    def put_user_into_group(cls, user, group):
        for instance in cls.objects.filter(group__school=group.school, user=user):
            instance.is_actual = False
            instance.save()
        cls(user=user, group=group).save()


def get_locked_timeout():
    return datetime.datetime.now() + settings.SISTEMA_ENTRANCE_CHECKING_TIMEOUT


class CheckingLock(models.Model):
    locked_user = models.ForeignKey(users.models.User, related_name='checking_locked')

    locked_by = models.ForeignKey(users.models.User, related_name='checking_lock')

    locked_until = models.DateTimeField(default=get_locked_timeout)


class SolutionScore(models.Model):
    solution = models.ForeignKey(EntranceExamTaskSolution, related_name='scores')

    scored_by = models.ForeignKey(users.models.User, related_name='+')

    score = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)


class CheckingComment(models.Model):
    school = models.ForeignKey(schools.models.School, related_name='+')

    user = models.ForeignKey(users.models.User, related_name='checking_comments')

    commented_by = models.ForeignKey(users.models.User, related_name='+')

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)


# Рекомендации от проверяющего по поступлению в определённую параллель
class EntranceRecommendation(models.Model):
    school = models.ForeignKey(schools.models.School, related_name='+')

    user = models.ForeignKey(users.models.User, related_name='entrance_recommendations')

    checked_by = models.ForeignKey(users.models.User, related_name='+')

    # Null parallel means recommendation to not enroll user
    parallel = models.ForeignKey(schools.models.Parallel, related_name='entrance_recommendations',
                                 blank=True,
                                 null=True,
                                 default=None)

    score = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)


class EntranceStatus(models.Model):
    class Status(djchoices.DjangoChoices):
        NOT_PARTICIPATED = djchoices.ChoiceItem(1, 'Не участвовал в конкурсе')
        AUTO_REJECTED = djchoices.ChoiceItem(2, 'Автоматический отказ')
        NOT_ENROLLED = djchoices.ChoiceItem(3, 'Не прошёл по конкурсу')
        ENROLLED = djchoices.ChoiceItem(4, 'Поступил')

    school = models.ForeignKey(schools.models.School, related_name='entrance_statuses')

    user = models.ForeignKey(users.models.User, related_name='entrance_statuses')

    # created_by=None means system's auto creating
    created_by = models.ForeignKey(users.models.User, blank=True, null=True, default=None)

    public_comment = models.TextField(help_text='Публичный комментарий. Может быть виден поступающему', blank=True)

    is_status_visible = models.BooleanField()

    status = models.IntegerField(choices=Status.choices, validators=[Status.validator])

    session = models.ForeignKey(schools.models.Session, blank=True, null=True, default=None)

    parallel = models.ForeignKey(schools.models.Parallel, blank=True, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User entrance statuses'
        unique_together = ('school', 'user')


class AbstractAbsenceReason(polymorphic.models.PolymorphicModel):
    school = models.ForeignKey(schools.models.School, related_name='absences_reasons')

    user = models.ForeignKey(users.models.User, related_name='absences_reasons')

    private_comment = models.TextField(blank=True, help_text='Не показывается школьнику')

    public_comment = models.TextField(blank=True, help_text='Показывается школьнику')

    created_by = models.ForeignKey(users.models.User, related_name='+', null=True, default=None,
                                   blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def for_user_in_school(cls, user, school):
        """Returns absence reason for specified user or None if user has not declined."""
        return cls.objects.filter(user=user, school=school).first()

    def default_public_comment(self):
        raise NotImplementedError()


class RejectionAbsenceReason(AbstractAbsenceReason):
    def __str__(self):
        return 'Отказ от участия'

    def default_public_comment(self):
        return 'Вы отказались от участия в ЛКШ.'


class NotConfirmedAbsenceReason(AbstractAbsenceReason):
    def __str__(self):
        return 'Участие не подтверждено'

    def default_public_comment(self):
        return 'Вы не подтвердили своё участие в ЛКШ.'