# -*- coding: utf-8 -*-

"""Tests for the dates app"""

import datetime
import unittest

import django.test
from django.db import IntegrityError

import users.models
from dates import models
from schools.models import School

TIMEZONE = datetime.timezone(datetime.timedelta())


class KeyDateTestCase(django.test.TestCase):
    def setUp(self):
        self.school_1 = School.objects.create(
            name="Test school 1",
            year='2048',
            short_name='school-1',
        )
        self.school_2 = School.objects.create(
            name="Test school 2",
            year='4096',
            short_name='school-2',
        )

        self.user_without_exception = users.models.User.objects.create_user(
            'test', 'test@test.com', 'password')
        self.user_with_exception = users.models.User.objects.create_user(
            'test2', 'test2@test.com', 'password')

        self.key_date = models.KeyDate.objects.create(
            name='New Year',
            short_name='new-year',
            datetime=datetime.datetime(2018, 1, 1, 0, 0, tzinfo=TIMEZONE),
            school=self.school_1,
        )

        models.UserKeyDateException.objects.create(
            key_date=self.key_date,
            user=self.user_with_exception,
            datetime=datetime.datetime(2018, 1, 2, 0, 0, tzinfo=TIMEZONE)
        )

    @unittest.mock.patch(
        'django.utils.timezone.now',
        new=lambda: datetime.datetime(2017, 12, 31, 23, 59, tzinfo=TIMEZONE)
    )
    def test_key_date_not_passed(self):
        """The case when key date is not passed is handled correctly"""

        self.assertFalse(
            self.key_date.passed_for_user(self.user_without_exception)
        )

    @unittest.mock.patch(
        'django.utils.timezone.now',
        new=lambda: datetime.datetime(2018, 1, 1, 0, 1, tzinfo=TIMEZONE)
    )
    def test_key_date_passed(self):
        """The case when key date is passed is handled correctly"""

        self.assertTrue(
            self.key_date.passed_for_user(self.user_without_exception)
        )

    @unittest.mock.patch(
        'django.utils.timezone.now',
        new=lambda: datetime.datetime(2018, 1, 1, 23, 59, tzinfo=TIMEZONE)
    )
    def test_key_date_exception_works(self):
        """The case when exception prolongs a key date is handled correctly"""

        self.assertFalse(
            self.key_date.passed_for_user(self.user_with_exception)
        )

    def test_clone_fail_if_school_and_short_name_not_unique(self):
        """Clone fails if new key date's school and short_name are not set"""
        with self.assertRaises(IntegrityError):
            self.key_date.clone()

    def test_clone_keeping_field_values(self):
        """Key date is cloned and all field values are copied correctly"""
        new_date = self.key_date.clone(short_name='that-moment')
        self.assertIsNotNone(new_date.pk)
        self.assertNotEqual(new_date.pk, self.key_date.pk)
        self.assertEqual(new_date.school, self.key_date.school)
        self.assertEqual(new_date.short_name, 'that-moment')
        self.assertEqual(new_date.name, self.key_date.name)

    def test_clone_with_custom_field_values(self):
        """Clone with specified field values correctly sets the fields"""
        apocalypse_datetime = datetime.datetime(9999, 3, 20)
        new_date = self.key_date.clone(
            school=None,
            name='Apocalypse',
            short_name='apocalypse',
            datetime=apocalypse_datetime,
        )
        self.assertIsNone(new_date.school)
        self.assertEqual(new_date.name, 'Apocalypse')
        self.assertEqual(new_date.short_name, 'apocalypse')
        self.assertEqual(new_date.datetime, apocalypse_datetime)

    def test_clone_to_another_school(self):
        """Key date is correctly copied to another school"""
        new_date = self.key_date.clone(school=self.school_2)
        self.assertEqual(new_date.school, self.school_2)
        self.assertEqual(new_date.short_name, self.key_date.short_name)

    def test_clone_exceptions(self):
        """Exceptions are copied to the freshly cloned key date"""
        src_date = models.KeyDate.objects.create(
            school=self.school_1,
            short_name='birthday',
            name='Happy birthday!',
            datetime=datetime.datetime(2000, 1, 1, tzinfo=TIMEZONE),
        )

        einstein = users.models.User.objects.create_user(
            'einstein', 'einstein@example.org', 'password')
        models.UserKeyDateException.objects.create(
            key_date=src_date,
            user=einstein,
            datetime=datetime.datetime(1879, 3, 14, tzinfo=TIMEZONE)
        )

        feynman = users.models.User.objects.create_user(
            'feynman', 'feynman@example.org', 'password')
        feynman_birthday = datetime.datetime(1918, 5, 11, tzinfo=TIMEZONE)
        models.UserKeyDateException.objects.create(
            key_date=src_date,
            user=feynman,
            datetime=feynman_birthday,
        )

        new_date = src_date.clone(
            short_name='that-moment',
            copy_exceptions=True,
        )
        self.assertEqual(src_date.user_exceptions.count(), 2)
        self.assertEqual(new_date.user_exceptions.count(), 2)
        exception = new_date.user_exceptions.get(user=feynman)
        self.assertEqual(exception.datetime, feynman_birthday)
