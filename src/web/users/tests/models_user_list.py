# -*- coding: utf-8 -*-

"""Tests for users.models.UserList."""

from django.test import TestCase

import users.models

class UserListTestCase(TestCase):
    def setUp(self):
        self.user1 = users.models.User.objects.create_user(
            'user1', 'user1@test.org', 'password')
        self.user2 = users.models.User.objects.create_user(
            'user2', 'user2@test.org', 'password')
        self.user3 = users.models.User.objects.create_user(
            'user3', 'user3@test.org', 'password')

        self.user_list = users.models.UserList.objects.create(name='Test list')
        self.user_list.users.add(self.user1)
        self.user_list.users.add(self.user2)

    def test_list_contains_correct_users(self):
        self.assertTrue(self.user_list.contains_user(self.user1))
        self.assertTrue(self.user_list.contains_user(self.user2))

        self.assertFalse(self.user_list.contains_user(self.user3))
