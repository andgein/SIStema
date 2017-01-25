# -*- coding: utf-8 -*-

"""Tests for poldnev.models.Role."""

import unittest

import django.test

# TODO(Artem Tabolin): find a way not to depend on location of poldnev module
import modules.poldnev.models as models


class RoleTestCase(django.test.TestCase):
    def setUp(self):
        self.session = models.Session.objects.create(
            poldnev_id='0871',
            name='2008.Кострома')
        self.role = models.Role.objects.create(
            session=self.session,
            poldnev_role='C3.преп')

    def test_str(self):
        """Role's string representation should be correct."""
        self.assertEqual(str(self.role), '2008.Кострома: C3.преп')
