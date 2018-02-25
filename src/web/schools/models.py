# -*- coding: utf-8 -*-

from django.urls import reverse
from django.db import models
import django.utils.dateformat

from constance import config

import users.models


class School(models.Model):
    name = models.CharField(max_length=50, help_text='Например, «ЛКШ 2048»')

    year = models.CharField(
        max_length=50,
        blank=True,
        help_text='Год (календарный или учебный) проведения школы. Для '
                  'ЛКШ.Зима может отличаться от short_name. Может быть '
                  'не уникальным.')

    full_name = models.TextField(
        help_text='Полное название, не аббревиатура. По умолчанию совпадает с '
                  'обычным названием. Например, «Летняя компьютерная школа '
                  '2048»')

    short_name = models.CharField(
        max_length=20,
        help_text='Используется в урлах. Например, 2048',
        unique=True)

    is_public = models.BooleanField(
        default=False,
        help_text='Открыт ли доступ к школе юзерам без админских прав')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # TODO(Artem Tabolin): looks like schools app should know nothing about
        #                      school namespace.
        return reverse('school:index', kwargs={'school_name': self.short_name})

    def get_staff_url(self):
        # TODO(Artem Tabolin): looks like schools app should know nothing about
        #                      school namespace.
        return reverse('school:staff', kwargs={'school_name': self.short_name})

    def get_user_url(self):
        # TODO(Artem Tabolin): looks like schools app should know nothing about
        #                      school namespace.
        return reverse('school:user', kwargs={'school_name': self.short_name})

    @classmethod
    def get_current_school(cls):
        return cls.objects.get(
            short_name=config.SISTEMA_CURRENT_SCHOOL_SHORT_NAME)


class Session(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    name = models.CharField(
        max_length=50,
        blank=True,
        help_text='Например, Август. Можно оставить пустым, если это '
                  'единственная смена.')

    short_name = models.CharField(
        max_length=20,
        blank=True,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием. Можно оставить пустым, если это '
                  'единственная смена. Например, august.')

    start_date = models.DateField(help_text='Первый день смены')

    finish_date = models.DateField(help_text='Последний день смены')

    class Meta:
        unique_together = ('school', 'short_name')

    def __str__(self):
        if not self.name:
            return self.school.name
        return '%s.%s' % (self.school.name, self.name)

    def get_full_name(self):
        if not self.name:
            return self.school.name
        return '%s.%s' % (self.school.name, self.name)

    @property
    def dates_range(self):
        """Return natural language representation of the session dates range."""
        date_format = django.utils.dateformat.format

        # С 27 декабря 2015 года по 7 января 2016 года
        if self.start_date.year != self.finish_date.year:
            return 'С %s по %s' % (date_format(self.start_date, 'j E Y года'),
                                   date_format(self.finish_date, 'j E Y года'))

        # С 28 июля по 20 августа 2016 года
        if self.start_date.month != self.finish_date.month:
            return 'С %s по %s' % (date_format(self.start_date, 'j E'),
                                   date_format(self.finish_date, 'j E Y года'))

        # С 5 по 20 июля 2016 года
        return 'С %s по %s' % (date_format(self.start_date, 'j'),
                               date_format(self.finish_date, 'j E Y года'))


class Parallel(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='parallels',
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием. Например, c_prime.')

    name = models.CharField(max_length=100, help_text='Например, C\'')

    sessions = models.ManyToManyField(Session)

    class Meta:
        unique_together = ('school', 'short_name')

    def __str__(self):
        return '%s.%s' % (self.school.name, self.name)


class Group(models.Model):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='groups',
    )

    parallel = models.ForeignKey(
        Parallel,
        on_delete=models.CASCADE,
        related_name='groups',
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием. Например, c5.')

    name = models.CharField(max_length=100, help_text='Например, C5')

    class Meta:
        unique_together = ('session', 'parallel', 'short_name')

    def __str__(self):
        return '{}.{}'.format(self.session, self.name)

    def save(self, *args, **kwargs):
        if self.parallel.school_id != self.session.school_id:
            raise ValueError(
                'Error while saving study group: parallel ({}) and session '
                '({}) should belong to the same school.'
                .format(self.parallel, self.session)
            )
        super().save(*args, **kwargs)


class SchoolParticipant(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='participants',
    )

    user = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='school_participations',
    )

    parallel = models.ForeignKey(
        Parallel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='participants',
    )

    # TODO: Add group

    class Meta:
        unique_together = ('school', 'user')

    def __str__(self):
        return self.user.get_full_name()

    @classmethod
    def for_user_in_school(cls, user, school):
        return cls.objects.filter(user=user, school=school).first()
