# -*- coding: utf-8 -*-

"""Tests for school.models.Session."""

import datetime

import django.test

import schools.models as models


class SessionTestCase(django.test.TestCase):
    def setUp(self):
        school = models.School.objects.create(name='ЛКШ 100500',
                                              year='100500',
                                              short_name='sis-100500')
        models.Session.objects.create(school=school,
                                      name='Сентябрь',
                                      short_name='september',
                                      start_date=datetime.date(1916, 9, 3),
                                      finish_date=datetime.date(1916, 9, 24))
        models.Session.objects.create(school=school,
                                      name='Октябрь',
                                      short_name='october',
                                      start_date=datetime.date(1916, 9, 27),
                                      finish_date=datetime.date(1916, 10, 18))
        models.Session.objects.create(school=school,
                                      name='Жизнь',
                                      short_name='live',
                                      start_date=datetime.date(1992, 6, 11),
                                      finish_date=datetime.date(2016, 12, 17))

    def test_dates_range(self):
        """dates_range() should return the correct natural language
        representation for different possible ranges."""
        september = models.Session.objects.get(
            school__short_name='sis-100500', short_name='september')
        self.assertEqual(september.dates_range, 'С 3 по 24 сентября 1916 года')

        october = models.Session.objects.get(
            school__short_name='sis-100500', short_name='october')
        self.assertEqual(october.dates_range,
                         'С 27 сентября по 18 октября 1916 года')

        live = models.Session.objects.get(
            school__short_name='sis-100500', short_name='live')
        self.assertEqual(live.dates_range,
                         'С 11 июня 1992 года по 17 декабря 2016 года')

    def test_str(self):
        """Session's string representation should be of the form
        '<school_name>.<session_name>'."""
        session = models.Session.objects.get(
            school__short_name='sis-100500', short_name='september')
        self.assertEqual(str(session), 'ЛКШ 100500.Сентябрь')
