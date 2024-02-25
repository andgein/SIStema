# -*- coding: utf-8 -*-

"""Tests for school.models.Parallel."""

import datetime

import django.test

import schools.models as models


class ParallelTestCase(django.test.TestCase):
    def setUp(self):
        school = models.School.objects.create(name='ЛКШ 100500',
                                              year='100500',
                                              short_name='sis-100500')
        session = models.Session.objects.create(school=school,
                                      name='Сентябрь',
                                      short_name='september',
                                      start_date=datetime.date(1916, 9, 3),
                                      finish_date=datetime.date(1916, 9, 24))
        parallel = models.Parallel.objects.create(school=school,
                                                  short_name='e_prime',
                                                  name="E'")
        parallel.sessions.add(session)


    def test_str(self):
        """Parallels's string representation should be of the form
        '<school_name>.<parallel_name>'."""
        parallel = models.Parallel.objects.get(
            school__short_name='sis-100500', short_name='e_prime')
        self.assertEqual(str(parallel), "ЛКШ 100500.E'")
