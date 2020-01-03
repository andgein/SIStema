from django.db import models
from django.utils.translation import gettext_lazy as _


class Problem(models.Model):
    """This model contains meta information about Polygon problem"""

    polygon_id = models.IntegerField(
        primary_key=True,
        verbose_name=_('ID'),
        help_text='ID задачи в полигоне',
    )

    name = models.CharField(
        max_length=120,
        verbose_name=_('name'),
        help_text='Короткое имя задачи в полигоне',
    )

    owner = models.CharField(
        max_length=120,
        verbose_name=_('owner'),
        help_text='Владелец задачи в полигоне',
    )

    deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Была ли задача удалена',
    )

    revision = models.IntegerField(
        verbose_name=_('revision'),
        help_text='Номер последней ревизии задачи',
    )

    latest_package = models.IntegerField(
        verbose_name=_('latest package'),
        blank=True,
        null=True,
        help_text='Максимальный номер ревизии задачи, для которой собран пакет',
    )

    input_file = models.CharField(
        max_length=120,
        verbose_name=_('input file'),
        help_text='Имя входного файла',
    )

    output_file = models.CharField(
        max_length=120,
        verbose_name=_('output file'),
        help_text='Имя выходного файла',
    )

    time_limit = models.IntegerField(
        verbose_name=_('time limit (ms)'),
        help_text='Ограничение по времени в миллисекундах',
    )

    memory_limit = models.IntegerField(
        verbose_name=_('memory limit (bytes)'),
        help_text='Ограничение по памяти в байтах',
    )

    interactive = models.BooleanField(
        verbose_name=_('interactive?'),
        help_text='Является ли задача интерактивной',
    )

    tags = models.ManyToManyField(
        'polygon.Tag',
        related_name='problems',
        verbose_name=_('tags'),
    )

    general_description = models.TextField(
        verbose_name=_('general description'),
        help_text='Краткое описание задачи',
    )

    general_tutorial = models.TextField(
        verbose_name=_('general tutorial'),
        help_text='Краткое описание решения задачи',
    )

    class Meta:
        verbose_name = _('problem')
        verbose_name_plural = _('problems')

    def __str__(self):
        return '{}:{}'.format(self.name, self.polygon_id)


class Tag(models.Model):
    """Tag for problem in Polygon"""

    tag = models.CharField(
        max_length=120,
        primary_key=True,
        verbose_name=_('tag'),
    )

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')


class Contest(models.Model):
    """This model contains meta information about Polygon contest"""

    polygon_id = models.IntegerField(
        primary_key=True,
        verbose_name=_('ID'),
        help_text='ID контеста в полигоне',
    )

    name = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_('name'),
        help_text='Имя контеста в полигоне',
    )

    class Meta:
        verbose_name = _('contest')
        verbose_name_plural = _('contests')


class ProblemInContest(models.Model):
    """Relation between contests and problems"""

    contest = models.ForeignKey(
        'polygon.Contest',
        on_delete=models.CASCADE,
        related_name='problem_entries',
        verbose_name=_('contest'),
    )

    index = models.CharField(
        max_length=32,
        verbose_name=_('index'),
        help_text='Индекс задачи в контесте (например, A, B, C, ...)',
    )

    problem = models.ForeignKey(
        'polygon.Problem',
        on_delete=models.CASCADE,
        related_name='contest_entries',
        verbose_name=_('problem'),
    )

    class Meta:
        verbose_name = _('problem in contest')
        verbose_name_plural = _('problem in contests')
        unique_together = ('contest', 'problem')
