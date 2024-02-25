# -*- coding: utf-8 -*-

"""Tests for poldnev.models.Person."""


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
        """Person's full name should be correct."""
        self.assertEqual(self.person.full_name, 'Матюхин Виктор Александрович')
