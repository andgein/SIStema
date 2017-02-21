# -*- coding: utf-8 -*-

"""Tests for schools.views."""

import unittest

import django.test

from schools import models
from schools import views
import users.models

class ViewsTestCase(django.test.TestCase):
    def setUp(self):
        self.request_factory = django.test.RequestFactory()
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
        self.school = models.School.objects.create(name='ЛКШ 100500',
                                                   year='100500',
                                                   short_name='sis-100500')

    @unittest.mock.patch('schools.views.user')
    def test_index_for_student(self, user_view_mock):
        """Index returns correct page for student"""
        request = self.request_factory.get('/sis-100500/')
        request.user = self.student
        request.school = self.school
        views.index(request)
        user_view_mock.assert_called_once_with(request)

    @unittest.mock.patch('schools.views.staff')
    def test_index_for_teacher(self, staff_view_mock):
        """Index returns correct page for student"""
        request = self.request_factory.get('/sis-100500/')
        request.user = self.teacher
        request.school = self.school
        views.index(request)
        staff_view_mock.assert_called_once_with(request)

    @unittest.mock.patch('django.shortcuts.redirect')
    def test_staff(self, redirect_mock):
        """Staff view makes correct redirect"""
        request = self.request_factory.get('/sis-100500/')
        request.user = self.teacher
        request.school = self.school
        views.staff(request)
        redirect_mock.assert_called_once_with('school:entrance:enrolling',
                                              school_name='sis-100500')

    # TODO(Artem Tabolin): test the case with some blocks
    @unittest.mock.patch('django.shortcuts.render')
    def test_user_no_blocks(self, render_mock):
        """User view renders correct template with correct arguments"""
        request = self.request_factory.get('/sis-100500/')
        request.user = self.student
        request.school = self.school
        views.user(request)
        render_mock.assert_called_once_with(
            request,
            'home/user.html',
            {'school': self.school, 'blocks': []})
