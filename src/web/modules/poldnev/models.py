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
        return self.full_name

    @property
    def full_name(self):
        return ' '.join([self.last_name, self.first_name, self.middle_name])

    @property
    def url(self):
        return 'https://poldnev.ru/lksh/id' + str(self.poldnev_id)

    @property
    def last_role(self):
        if not hasattr(self, '_last_role'):
            self._last_role = self.history_entries.order_by('-role__session__poldnev_id').first().role
        return self._last_role


class Role(models.Model):
    """Role for person in session from poldnev.ru"""

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        help_text='Смена из модуля schools, соответствующая этой смене на '
                  'poldnev.ru')

    poldnev_role = models.CharField(
        max_length=150,
        help_text='Строка, обозначающая роль на poldnev.ru. Заполняется '
                  'автоматически командой manage.py update_poldnev по '
                  'информации с сайта.')

    @classmethod
    def make_id(cls, session_id, poldnev_role):
        return session_id + ':' + poldnev_role

    def __str__(self):
        return self.session.name + ': ' + self.poldnev_role

    @property
    def role_id(self):
        return self.make_id(self.session.poldnev_id, self.poldnev_role)


class HistoryEntry(models.Model):
    """The history entry from poldnev.ru

    Means that person participated in session in some role."""

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        help_text='Человек',
        related_name='history_entries',
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        help_text='Роль. Также содержит информацию о смене.',
        related_name='history_entries',
    )

    def __str__(self):
        return '{} ({})'.format(self.person, self.role)

    @property
    def entry_id(self):
        return str(self.person.poldnev_id) + ':' + self.role.role_id

    @property
    def url(self):
        return 'https://poldnev.ru/lksh/id{}#{}'.format(
            self.person.poldnev_id, self.role.session.poldnev_id)
