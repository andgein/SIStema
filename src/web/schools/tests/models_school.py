# -*- coding: utf-8 -*-

"""Tests for school.models.School."""

import django.test

import schools.models as models


class SchoolTestCase(django.test.TestCase):
    def setUp(self):
        models.School.objects.create(name='ЛКШ 100500',
                                     year='100500',
                                     short_name='sis-100500')

    def test_default_full_name(self):
        """full_name should be set to the value of name by default."""
        school = models.School.objects.get(short_name='sis-100500')
        self.assertEqual(school.name, school.full_name)

    def test_get_absolute_url(self):
        """School's get_absolute_url should return a correct url."""
        school = models.School.objects.get(short_name='sis-100500')
        self.assertEqual(school.get_absolute_url(), '/sis-100500/')

    def test_str(self):
        """School's string representation should be equal to its name."""
        school = models.School.objects.get(short_name='sis-100500')
        self.assertEqual(str(school), school.name)
