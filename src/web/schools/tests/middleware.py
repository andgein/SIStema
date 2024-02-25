# -*- coding: utf-8 -*-

"""Tests for schools.middleware."""

import unittest

import django.test
from django.http import response

from schools import models
from schools import middleware
import users.models


class SchoolMiddlewareTestCase(django.test.TestCase):
    def setUp(self):
        self.request_factory = django.test.RequestFactory()
        self.middleware = middleware.SchoolMiddleware(lambda request: None)
        self.student = users.models.User.objects.create(
            username='test_student',
            email='student@lksh.ru',
            password='student_secret',
            is_staff=False)
        self.teacher = users.models.User.objects.create(
            username='test_teacher',
            email='teacher@lksh.ru',
            password='teacher_secret',
            is_staff=True)
        self.public_school = models.School.objects.create(name='ЛКШ 100500',
                                                          year='100500',
                                                          short_name='sis-100500',
                                                          is_public=True)
        self.private_school = models.School.objects.create(name='ЛКШ 100501',
                                                           year='100501',
                                                           short_name='sis-100501',
                                                           is_public=False)

    def test_student_and_public_school(self):
        request = self.request_factory.get('/')
        request.user = self.student
        kwargs = {'school_name': self.public_school.short_name}
        self.assertIsNone(self.middleware.process_view(request, None, None, kwargs))
        self.assertEqual(request.school, self.public_school)

    @unittest.expectedFailure(response.Http404)
    def test_student_and_private_school(self):
        request = self.request_factory.get('/')
        request.user = self.student
        kwargs = {'school_name': self.private_school.short_name}
        self.middleware.process_view(request, None, None, kwargs)
        self.assertTrue(False)  # assertFail

    def test_teacher_and_public_school(self):
        request = self.request_factory.get('/')
        request.user = self.teacher
        kwargs = {'school_name': self.public_school.short_name}
        self.assertIsNone(self.middleware.process_view(request, None, None, kwargs))
        self.assertEqual(request.school, self.public_school)

    def test_teacher_and_private_school(self):
        request = self.request_factory.get('/')
        request.user = self.teacher
        kwargs = {'school_name': self.private_school.short_name}
        self.assertIsNone(self.middleware.process_view(request, None, None, kwargs))
        self.assertEqual(request.school, self.private_school)
