from django.core import urlresolvers
from django.db import models
import school.models
import modules.ejudge.models
import user.models


class EntranceExamTask(models.Model):
    title = models.CharField(max_length=100, help_text='Название')

    text = models.TextField(help_text='Формулировка задания')

    exam = models.ForeignKey('EntranceExam', related_name='%(class)s')

    help_text = models.CharField(max_length=100,
                                 help_text='Дополнительная информация, например, сведения о формате ответа',
                                 blank=True)

    def __str__(self):
        return self.title

    def get_child_object(self):
        child = [TestEntranceExamTask, FileEntranceExamTask, ProgramEntranceExamTask]
        for children in child:
            class_name = children.__name__.lower()
            if hasattr(self, class_name):
                return getattr(self, class_name)

        return None


class TestEntranceExamTask(EntranceExamTask):
    correct_answer_re = models.CharField(max_length=100, help_text='Правильный ответ (регулярное выражение)')

    validation_re = models.CharField(max_length=100,
                                     help_text='Регулярное выражение для валидации ввода',
                                     blank=True)


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


class EntranceExam(models.Model):
    for_school = models.OneToOneField(school.models.School)

    def __str__(self):
        return 'Вступительная работа для %s' % self.for_school

    def get_absolute_url(self):
        return urlresolvers.reverse('school:entrance:exam', kwargs={ 'school_name': self.for_school.short_name })


class EntranceStep(models.Model):
    for_school = models.ForeignKey(school.models.School, related_name='entrance_steps')

    class_name = models.CharField(max_length=100, help_text='Путь до класса, описывающий шаг')

    params = models.TextField(help_text='Параметры для шага')

    order = models.IntegerField()

    def __str__(self):
        return 'Шаг %s используется для %s' % (self.class_name, self.for_school)

    class Meta:
        ordering = ['order']


class EntranceLevel(models.Model):
    """
    Уровень вступительной работы.
    Для каждой задачи могут быть указаны уровни, для которых она предназначена.
    Уровень школьника определяется с помощью EntranceLevelLimiter'ов (например, на основе тематической анкеты
    из модуля topics или прошлой учёбы в других параллелях)
    """
    for_school = models.ForeignKey(school.models.School)

    short_name = models.CharField(max_length=100,
                                  help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')

    name = models.CharField(max_length=100)

    order = models.IntegerField(default=0)

    tasks = models.ManyToManyField(EntranceExamTask, blank=True)

    def __str__(self):
        return 'Уровень вступительной работы «%s» для %s' % (self.name, self.for_school)

    class Meta:
        ordering = ['for_school_id', 'order']


class EntranceExamTaskSolution(models.Model):
    task = models.ForeignKey(EntranceExamTask)

    user = models.ForeignKey(user.models.User)

    solution = models.TextField()

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


class EntranceUserUpgrade(models.Model):
    user = models.ForeignKey(user.models.User)

    for_school = models.ForeignKey(school.models.School, related_name='%(class)s')
