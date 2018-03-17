# -*- coding: utf-8 -*-

from django import conf
from django.db import models
import schools.models


class Session(models.Model):
    """SIS session from poldnev.ru"""

    poldnev_id = models.CharField(
        primary_key=True,
        max_length=50,
        help_text='Id смены на poldnev.ru. Заполняется автоматически командой '
                  'manage.py update_poldnev по информации с сайта.')

    name = models.CharField(
        max_length=50,
        help_text='Имя смены на poldnev.ru. Заполняется автоматически командой '
                  'manage.py update_poldnev по информации с сайта.')

    schools_session = models.OneToOneField(
        schools.models.Session,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='poldnev_session',
        help_text='Смена из модуля schools, соответствующая этой смене на '
                  'poldnev.ru')

    verified = models.BooleanField(
        default=False,
        help_text='True, если корректность значения schools_session была '
                  'проверена человеком')

    url = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ('-poldnev_id',)

    def __str__(self):
        return self.name


class Parallel(models.Model):
    """SIS parallel from poldnev.ru"""

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        help_text='Смена',
        related_name='parallels',
    )

    name = models.CharField(
        max_length=100,
        help_text='Название'
    )

    schools_parallel = models.ForeignKey(
        schools.models.Parallel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='poldnev_parallels',
        help_text='Параллель из модуля schools, соответствующая этой параллели '
                  'на poldnev.ru'
    )

    def __str__(self):
        return '{} {}'.format(self.session, self.name)

    @property
    def unique_key(self):
        return '{}:{}'.format(self.session.poldnev_id, self.name)

    @property
    def url(self):
        return '%s/%s' % (self.session.url, self.name)

    class Meta:
        unique_together = ('session', 'name')
        ordering = ('session', 'name')


class StudyGroup(models.Model):
    """SIS study group from poldnev.ru"""

    parallel = models.ForeignKey(
        Parallel,
        on_delete=models.CASCADE,
        help_text='Параллель',
        related_name='study_groups',
    )

    name = models.CharField(
        max_length=100,
        help_text='Название'
    )

    schools_group = models.OneToOneField(
        schools.models.Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='poldnev_group',
        help_text='Группа из модуля schools, соответствующая этой группе на '
                  'poldnev.ru'
    )

    def __str__(self):
        return '{} {}'.format(self.parallel, self.name)

    @property
    def unique_key(self):
        return '{}:{}'.format(self.parallel.unique_key, self.name)

    class Meta:
        unique_together = ('parallel', 'name')
        ordering = ('parallel', 'name')


class Person(models.Model):
    """SIS person from poldnev.ru"""

    poldnev_id = models.IntegerField(
        primary_key=True,
        help_text='Id человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    first_name = models.CharField(
        max_length=100,
        help_text='Имя человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    middle_name = models.CharField(
        max_length=100,
        help_text='Отчество человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    last_name = models.CharField(
        max_length=200,
        help_text='Фамилия человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    user = models.OneToOneField(
        conf.settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='poldnev_person',
        help_text='Пользователь, соответствующий этому человеку на poldnev.ru')

    verified = models.BooleanField(
        default=False,
        help_text='True, если корректность значения user была проверена '
                  'человеком')

    class Meta:
        ordering = ('last_name', 'first_name', 'middle_name')

    def __str__(self):
        return '{} ({})'.format(self.full_name, self.poldnev_id)

    @property
    def full_name(self):
        return ' '.join([self.last_name, self.first_name, self.middle_name])

    @property
    def url(self):
        return 'https://poldnev.ru/lksh/id' + str(self.poldnev_id)

    @property
    def last_history_entry(self):
        if not hasattr(self, '_last_role'):
            self._last_history_entry = self.history_entries.order_by('-session__poldnev_id').first()
        return self._last_history_entry


class HistoryEntry(models.Model):
    """The history entry from poldnev.ru

    Means that person participated in session in some role."""

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        help_text='Человек',
        related_name='history_entries',
    )

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        help_text='Смена',
        related_name='history_entries',
    )

    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='history_entries',
        help_text='Учебная группа. Может отсутствовать, например, для врача',
        null=True,
        blank=True,
    )

    role = models.CharField(
        max_length=150,
        help_text='Роль. Пустая для школьников',
        blank=True,
    )

    def save(self, *args, **kwargs):
        if (self.session is not None
                and self.study_group is not None
                and self.study_group.parallel is not None
                and self.session != self.study_group.parallel.session):
            raise ValueError('poldnev.models.HistoryEntry: '
                             'study_group should belong to entry\'s session')
        super().save(*args, **kwargs)

    def __str__(self):
        return '{} ({}: {})'.format(self.person, self.session, self.full_role)

    @property
    def full_role(self):
        if not self.role:
            return self.study_group.name
        if not self.study_group:
            return self.role
        return '{}.{}'.format(self.study_group.name, self.role)

    @property
    def unique_key(self):
        return '{}:{}:{}'.format(self.person.poldnev_id, self.session.poldnev_id, self.full_role)

    @property
    def url(self):
        return 'https://poldnev.ru/lksh/id{}#{}'.format(
            self.person.poldnev_id, self.session.poldnev_id)

    class Meta:
        unique_together = ('session', 'study_group', 'role', 'person')
