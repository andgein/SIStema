# -*- coding: utf-8 -*-

"""Tests for users.models.User."""

import unittest

from django.test import TestCase
from users.models import User

class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(
            username='test_user_1',
            first_name='Семён',
            last_name='Печкин-Лавочкин',
            email='semen@pechkin-lavochkin.org')

        User.objects.create(
            username='test_user_2',
            last_name='Матроскин',
            email='matroskin@prostokvashino.ru')

        User.objects.create(
            username='test_user_3',
            first_name='James',
            email='james+bond@007.com')

    def test_get_full_name_both_names(self):
        """Full name should consist of first and last names separated by a
        space.
        """
        user = User.objects.get(username='test_user_1')
        self.assertEqual(user.get_full_name(), 'Семён Печкин-Лавочкин')

    def test_get_full_name_first_name_only(self):
        """Full name should consist of just the first name if the last name is
        not specified.
        """
        user = User.objects.get(username='test_user_3')
        self.assertEqual(user.get_full_name(), 'James')

    def test_get_full_name_last_name_only(self):
        """Full name should consist of just the last name if the first name is
        not specified.
        """
        user = User.objects.get(username='test_user_2')
        self.assertEqual(user.get_full_name(), 'Матроскин')

    def test_get_short_name(self):
        """Full name should consist of just the last name if the first name is
        not specified.
        """
        user = User.objects.get(username='test_user_1')
        self.assertEqual(user.get_short_name(), 'Семён')

    @unittest.mock.patch('django.core.mail.send_mail')
    def test_email_user(self, send_mail_mock):
        """Django's send_mail method should be called."""
        user = User.objects.get(username='test_user_1')
        user.email_user(
            subject='Testing',
            message='The test should succeed',
            from_email='test@example.org')

        send_mail_mock.assert_called_once_with(
            'Testing',
            'The test should succeed',
            'test@example.org',
            ['semen@pechkin-lavochkin.org'])

    def test_str(self):
        """String representation should be 'first_name last_name (email)'."""
        user = User.objects.get(username='test_user_1')
        self.assertEqual(
            str(user), 'Печкин-Лавочкин Семён (semen@pechkin-lavochkin.org)')

