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


class Tag(models.Model):
    """Tag for problem in Polygon"""

    tag = models.CharField(
        max_length=120,
        primary_key=True,
        verbose_name=_('tag'),
    )
