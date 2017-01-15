# -*- coding: utf-8 -*-

from django import conf
from django.db import models
import schools.models

class Session(models.Model):
    """SIS session from poldnev.ru"""

    poldnev_id = models.CharField(
        max_length=30,
        unique=True,
        help_text='Id смены на poldnev.ru. Заполняется автоматически командой '
                  'manage.py update_poldnev по информации с сайта.')

    name = models.CharField(
        max_length=30,
        help_text='Имя смены на poldnev.ru. Заполняется автоматически командой '
                  'manage.py update_poldnev по информации с сайта.')

    schools_session = models.OneToOneField(
        schools.models.Session,
        null=True,
        on_delete=models.SET_NULL,
        related_name='poldnev',
        help_text='Смена из модуля schools, соответствующая этой смене на '
                  'poldnev.ru')

    verified = models.BooleanField(
        default=False,
        help_text='True, если корректность значения schools_session была '
                  'проверена человеком')

    def __str__(self):
        return 'Session(poldnev_id={}, name={}, verified={})'.format(
            self.poldnev_id,
            self.name,
            self.verified)


class Person(models.Model):
    """SIS person from poldnev.ru"""

    poldnev_id = models.CharField(
        max_length=30,
        unique=True,
        help_text='Id человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    first_name = models.CharField(
        max_length=50,
        help_text='Имя человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    middle_name = models.CharField(
        max_length=50,
        help_text='Отчество человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    last_name = models.CharField(
        max_length=100,
        help_text='Фамилия человека на poldnev.ru. Заполняется автоматически '
                  'командой manage.py update_poldnev по информации с сайта.')

    user = models.OneToOneField(
        conf.settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='poldnev',
        help_text='Пользователь, соответствующий этому человеку на poldnev.ru')

    verified = models.BooleanField(
        default=False,
        help_text='True, если корректность значения user была проверена '
                  'человеком')

    def __str__(self):
        return 'Person(poldnev_id={}, name={}, verified={})'.format(
            self.poldnev_id,
            ' '.join([self.first_name, self.middle_name, self.last_name]),
            self.verified)


class Role(models.Model):
    """Role for person in session from poldnev.ru"""

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        help_text='Смена из модуля schools, соответствующая этой смене на '
                  'poldnev.ru')

    poldnev_role = models.CharField(
        max_length=50,
        help_text='Строка, обозначающая роль на poldnev.ru. Заполняется '
                  'автоматически командой manage.py update_poldnev по '
                  'информации с сайта.')

    def __str__(self):
        return 'Role(session_name={}, poldnev_role={})'.format(
            self.session.name,
            self.poldnev_role)


class HistoryEntry(models.Model):
    """The history entry from poldnev.ru

    Means that person participated in session in some role."""

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        help_text='Человек')

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        help_text='Роль. Также содержит информацию о смене.')

    def __str__(self):
        return 'HistoryEntry(person_id={}, session_id={}, role={})'.format(
            self.person.poldnev_id,
            self.role.session.poldnev_id,
            self.role.poldnev_role)
