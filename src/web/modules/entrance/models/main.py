import datetime
import re

import djchoices
import polymorphic.models
from django.core import urlresolvers
from django.conf import settings
from django.db import models, transaction
import django.utils.timezone
import sizefield.models

import schools.models
import modules.ejudge.models
import users.models
from modules.entrance import forms


class EntranceExamTask(polymorphic.models.PolymorphicModel):
    title = models.CharField(max_length=100, help_text='Название')

    text = models.TextField(help_text='Формулировка задания')

    exam = models.ForeignKey('EntranceExam', related_name='%(class)s')

    help_text = models.CharField(
        max_length=100,
        help_text='Дополнительная информация, например, сведения о формате '
                  'ответа',
        blank=True
    )

    order = models.IntegerField(
        help_text='Задачи выстраиваются по возрастанию порядка',
        default=0
    )

    max_score = models.PositiveIntegerField()

    custom_description = models.TextField(
        help_text='Текст с описанием типа задачи. Оставьте пустым, тогда будет '
                  'использован текст по умолчанию для данного вида задач. '
                  'В этом тексте можно указать, например, '
                  'для кого эта задача предназначена.\n'
                  'Поддерживается Markdown',
        blank=True,
    )

    def __str__(self):
        return self.title

    def is_solved_by_user(self, user):
        # Always not solved by default. Override when subclassing.
        return False

    @property
    def template_file(self):
        """
        Returns template file name in folder templates/entrance/exam/
        """
        raise NotImplementedError('Child should define property template_file')

    @property
    def type_title(self):
        """
        Returns title of blocks with these tasks
        """
        raise NotImplementedError('Child should define property type_title')

    def get_form(self, user_solutions, *args, **kwargs):
        """
        Returns form for this task with user_solutions as previous solutions.
        user_solutions are ordered by descending time
        """
        raise NotImplementedError('Child should define get_form()')

    @property
    def solution_class(self):
        raise NotImplementedError(
            'Child should define property solution_class'
        )


class TestEntranceExamTask(EntranceExamTask):
    template_file = 'test.html'
    type_title = 'Тестовые задания'

    correct_answer_re = models.CharField(max_length=100, help_text='Правильный ответ (регулярное выражение)')

    validation_re = models.CharField(max_length=100,
                                     help_text='Регулярное выражение для валидации ввода',
                                     blank=True)

    def check_solution(self, solution):
        return re.fullmatch(self.correct_answer_re, solution) is not None

    def is_solved_by_user(self, user):
        return self.solutions.filter(user=user).exists()

    def get_form(self, user_solutions, *args, **kwargs):
        initial = {}
        if len(user_solutions) > 0:
            initial['solution'] = user_solutions[0].solution
        form = forms.TestEntranceTaskForm(self, initial=initial, *args, **kwargs)
        if self.exam.is_closed():
            form['solution'].field.widget.attrs['readonly'] = True
        return form

    # Define it as property because TestEntranceExamTaskSolution
    # is not defined yet
    @property
    def solution_class(self):
        return TestEntranceExamTaskSolution


class FileEntranceExamTask(EntranceExamTask):
    template_file = 'file.html'
    type_title = 'Теоретические задачи'

    def is_solved_by_user(self, user):
        return self.solutions.filter(user=user).exists()

    def get_form(self, user_solutions, *args, **kwargs):
        return forms.FileEntranceTaskForm(self, *args, **kwargs)

    @property
    def solution_class(self):
        return FileEntranceExamTaskSolution


class EjudgeEntranceExamTask(EntranceExamTask):
    type_title = 'Практические задачи'

    ejudge_contest_id = models.PositiveIntegerField(
        help_text='ID контеста в еджадже'
    )

    ejudge_problem_id = models.PositiveIntegerField(
        help_text='ID задачи в еджадже'
    )

    def is_solved_by_user(self, user):
        user_solutions = self.solution_class.objects.filter(
            user=user,
            task=self
        ).select_related('ejudge_queue_element__submission__result')
        task_has_ok = any(filter(
            lambda s: s.is_checked and s.result.is_success,
            user_solutions
        ))
        return task_has_ok

    @property
    def solutions_template_file(self):
        raise NotImplementedError(
            'Child should define property solutions_template_file'
        )

    class Meta:
        abstract = True


class ProgramEntranceExamTask(EjudgeEntranceExamTask):
    template_file = 'program.html'
    solutions_template_file = '_program_solutions.html'

    input_file_name = models.CharField(max_length=100, blank=True)

    output_file_name = models.CharField(max_length=100, blank=True)

    time_limit = models.PositiveIntegerField(help_text='В миллисекундах')

    # Use FileSizeField to be able to define memory limit with units (i.e. 256M)
    memory_limit = sizefield.models.FileSizeField()

    input_format = models.TextField(blank=True)

    output_format = models.TextField(blank=True)

    def get_form(self, user_solutions, *args, **kwargs):
        return forms.ProgramEntranceTaskForm(self, *args, **kwargs)

    @property
    def solution_class(self):
        return ProgramEntranceExamTaskSolution


class OutputOnlyEntranceExamTask(EjudgeEntranceExamTask):
    template_file = 'output_only.html'
    solutions_template_file = '_output_only_solutions.html'

    def get_form(self, user_solutions, *args, **kwargs):
        return forms.OutputOnlyEntranceTaskForm(self, *args, **kwargs)

    @property
    def solution_class(self):
        return OutputOnlyEntranceExamTaskSolution


class EntranceExam(models.Model):
    school = models.OneToOneField(schools.models.School)

    close_time = models.DateTimeField(blank=True, default=None, null=True)

    def __str__(self):
        return 'Вступительная работа для %s' % self.school

    def is_closed(self):
        return (self.close_time is not None and
                django.utils.timezone.now() >= self.close_time)

    def get_absolute_url(self):
        return urlresolvers.reverse('school:entrance:exam', kwargs={
            'school_name': self.school.short_name
        })


class EntranceLevel(models.Model):
    """
    Уровень вступительной работы.
    Для каждой задачи могут быть указаны уровни, для которых она предназначена.
    Уровень школьника определяется с помощью EntranceLevelLimiter'ов (например,
    на основе тематической анкеты из модуля topics, класса в школе
    или учёбы в других параллелях в прошлые годы)
    """
    school = models.ForeignKey(schools.models.School)

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием'
    )

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


class EntranceLevelOverride(models.Model):
    """
    If present this level is used instead of dynamically computed one.
    """
    school = models.ForeignKey(schools.models.School, related_name='+')

    user = models.ForeignKey(users.models.User,
                             related_name='entrance_level_overrides')

    entrance_level = models.ForeignKey(EntranceLevel, related_name='overrides')

    class Meta:
        unique_together = ('school', 'user')

    def __str__(self):
        return 'Уровень {} для {}'.format(self.entrance_level, self.user)

    def save(self, *args, **kwargs):
        if self.school != self.entrance_level.school:
            raise ValueError(
                'Entrance level override should belong to the same school as '
                'its entrance level')
        super().save(*args, **kwargs)


class EntranceExamTaskSolution(polymorphic.models.PolymorphicModel):
    task = models.ForeignKey(
        EntranceExamTask,
        related_name='solutions'
    )

    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_exam_solutions'
    )

    solution = models.TextField()

    ip = models.CharField(
        max_length=50,
        help_text='IP-адрес, с которого было отправлено решение',
        default=''
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Решение %s по задаче %s' % (self.user, self.task)

    class Meta:
        ordering = ['-created_at']
        index_together = ('task', 'user')


class TestEntranceExamTaskSolution(EntranceExamTaskSolution):
    pass


class FileEntranceExamTaskSolution(EntranceExamTaskSolution):
    original_filename = models.TextField()


class EjudgeEntranceExamTaskSolution(EntranceExamTaskSolution):
    ejudge_queue_element = models.ForeignKey(modules.ejudge.models.QueueElement)

    @property
    def is_checked(self):
        return (self.ejudge_queue_element.status ==
                modules.ejudge.models.QueueElement.Status.CHECKED)

    @property
    def result(self):
        return self.ejudge_queue_element.get_result()

    class Meta:
        abstract = True


class ProgramEntranceExamTaskSolution(EjudgeEntranceExamTaskSolution):
    language = models.ForeignKey(modules.ejudge.models.ProgrammingLanguage)


class OutputOnlyEntranceExamTaskSolution(EjudgeEntranceExamTaskSolution):
    pass


class EntranceLevelUpgrade(models.Model):
    user = models.ForeignKey(users.models.User)

    upgraded_to = models.ForeignKey(EntranceLevel, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)


class EntranceLevelUpgradeRequirement(polymorphic.models.PolymorphicModel):
    base_level = models.ForeignKey(EntranceLevel, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)

    def is_met_by_user(self, user):
        # Always met by default. Override when subclassing.
        return True


class SolveTaskEntranceLevelUpgradeRequirement(EntranceLevelUpgradeRequirement):
    task = models.ForeignKey(EntranceExamTask, related_name='+')

    def is_met_by_user(self, user):
        return self.task.is_solved_by_user(user)


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

    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_recommendations'
    )

    checked_by = models.ForeignKey(users.models.User, related_name='+')

    # Null parallel means recommendation to not enroll user
    parallel = models.ForeignKey(
        schools.models.Parallel,
        related_name='entrance_recommendations',
        blank=True,
        null=True,
        default=None
    )

    score = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)


class EntranceStatus(models.Model):
    class Status(djchoices.DjangoChoices):
        NOT_PARTICIPATED = djchoices.ChoiceItem(1, 'Не участвовал в конкурсе')
        AUTO_REJECTED = djchoices.ChoiceItem(2, 'Автоматический отказ')
        NOT_ENROLLED = djchoices.ChoiceItem(3, 'Не прошёл по конкурсу')
        ENROLLED = djchoices.ChoiceItem(4, 'Поступил')
        PARTICIPATING = djchoices.ChoiceItem(5, 'Подал заявку')

    school = models.ForeignKey(
        schools.models.School,
        related_name='entrance_statuses'
    )

    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_statuses'
    )

    # created_by=None means system's auto creating
    created_by = models.ForeignKey(
        users.models.User,
        blank=True, null=True, default=None
    )

    public_comment = models.TextField(
        help_text='Публичный комментарий. Может быть виден поступающему',
        blank=True
    )

    is_status_visible = models.BooleanField(default=False)

    status = models.IntegerField(
        choices=Status.choices,
        validators=[Status.validator])

    session = models.ForeignKey(
        schools.models.Session,
        blank=True, null=True, default=None
    )

    parallel = models.ForeignKey(
        schools.models.Parallel,
        blank=True, null=True, default=None
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_enrolled(self):
        return self.status == self.Status.ENROLLED

    @classmethod
    def create_or_update(cls, school, user, status, **kwargs):
        with transaction.atomic():
            current = cls.objects.filter(school=school, user=user).first()
            if current is None:
                current = cls(school=school, user=user, status=status, **kwargs)
            else:
                current.status = status
                for key, value in current:
                    setattr(current, key, value)
            current.save()

    @classmethod
    def get_visible_status(cls, school, user):
        return cls.objects.filter(
            school=school,
            user=user,
            is_status_visible=True
        ).first()

    def __str__(self):
        return '%s %s' % (self.user, self.Status.values[self.status])

    class Meta:
        verbose_name_plural = 'User entrance statuses'
        unique_together = ('school', 'user')

# For using in templates
EntranceStatus.do_not_call_in_templates = True


class AbstractAbsenceReason(polymorphic.models.PolymorphicModel):
    school = models.ForeignKey(
        schools.models.School,
        related_name='absences_reasons'
    )

    user = models.ForeignKey(users.models.User, related_name='absences_reasons')

    private_comment = models.TextField(
        blank=True,
        help_text='Не показывается школьнику'
    )

    public_comment = models.TextField(
        blank=True,
        help_text='Показывается школьнику'
    )

    created_by = models.ForeignKey(
        users.models.User,
        related_name='+',
        null=True, default=None, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def for_user_in_school(cls, user, school):
        """
        Returns absence reason for specified user
        or None if user has not declined.
        """
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
