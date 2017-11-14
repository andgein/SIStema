# -*- coding: utf-8 -*-

"""Tests for the dates app"""

import datetime
import unittest

import django.test

from dates import models
import users.models


TIMEZONE = datetime.timezone(datetime.timedelta())


class KeyDateTestCase(django.test.TestCase):
    def setUp(self):
        self.user_without_exception = users.models.User.objects.create_user(
            'test', 'test@test.com', 'password')
        self.user_with_exception = users.models.User.objects.create_user(
            'test2', 'test2@test.com', 'password')

        self.key_date = models.KeyDate.objects.create(
            name='New Year',
            datetime=datetime.datetime(2018, 1, 1, 0, 0, tzinfo=TIMEZONE)
        )

        models.KeyDateException.objects.create(
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
