# -*- coding: utf-8 -*-

"""Tests for users.models.UserProfile."""

import unittest
import unittest.mock

from django.test import TestCase
from users.models import UserProfile, User

import datetime


class UserProfileTestCase(TestCase):

    def test_get_set_class(self):
        user_profile = UserProfile()
        start_date = datetime.date(year=2016, month=9, day=1)
        for i in range(365):
            date = start_date + datetime.timedelta(days=i)
            cur_class = (i * 17 + i * 9 + 13) % 100
            user_profile.set_class(cur_class, date)
            self.assertEqual(cur_class, user_profile.get_class(date))
            self.assertEqual(2016 - cur_class, user_profile.get_zero_class_year())

    def test_auto_increment_class(self):
        user_profile = UserProfile()
        start_date = datetime.date(year=2016, month=9, day=1)
        start_class = 8
        user_profile.set_class(start_class, start_date)
        for i in range(365 * 3):
            date = start_date + datetime.timedelta(days=i)
            self.assertEqual(start_class + i // 365, user_profile.get_class(date))

    def test_save_load_class(self):
        user = User()
        user_profile = UserProfile(user=user)
        start_date = datetime.date(year=2016, month=9, day=1)
        start_class = 8
        user_profile.set_class(start_class, start_date)
        user_profile.save()

        user_profile.refresh_from_db()
        new_date = datetime.date(year=2017, month=10, day=3)
        self.assertEqual(start_class + 1, user_profile.get_class(new_date))

    def test_current_class(self):
        user_profile = UserProfile()
        start_class = 8
        start_date = datetime.date(year=2016, month=9, day=1)
        with unittest.mock.patch('datetime.date') as mock_date:
            mock_date.today.return_value = start_date
            user_profile.current_class = start_class
            for i in range(365 * 3):
                mock_date.today.return_value = start_date + datetime.timedelta(days=i)
                self.assertEqual(start_class + i // 365, user_profile.current_class)

    def test_class_none(self):
        user_profile = UserProfile()
        self.assertIsNone(user_profile.current_class)
        self.assertIsNone(user_profile.get_zero_class_year())
        user_profile.current_class = 8
        self.assertIsNotNone(user_profile.current_class)
        self.assertIsNotNone(user_profile.get_zero_class_year())
        user_profile.current_class = None
        self.assertIsNone(user_profile.current_class)
        self.assertIsNone(user_profile.get_zero_class_year())

