# -*- coding: utf-8 -*-

"""Tests for poldnev.models.Session."""


import django.test

# TODO(Artem Tabolin): find a way not to depend on location of poldnev module
import modules.poldnev.models as models


class SessionTestCase(django.test.TestCase):
    def setUp(self):
        self.session = models.Session.objects.create(
            poldnev_id='0871',
            name='2008.Кострома')

    def test_str(self):
        """Session's string representation should be correct."""
        self.assertEqual(str(self.session), '2008.Кострома')
