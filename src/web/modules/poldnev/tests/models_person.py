# -*- coding: utf-8 -*-

"""Tests for poldnev.models.Person."""

import unittest

import django.test

# TODO(Artem Tabolin): find a way not to depend on location of poldnev module
import modules.poldnev.models as models


class PersonTestCase(django.test.TestCase):
    def setUp(self):
        self.person = models.Person.objects.create(
            poldnev_id='1',
            first_name='Виктор',
            middle_name='Александрович',
            last_name='Матюхин')

    def test_str(self):
        """Person's string representation should be correct."""
        self.assertEqual(str(self.person), 'Матюхин Виктор Александрович')
