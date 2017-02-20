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
        self.schools = [models.School.objects.create(name='ЛКШ 100500',
                                                     year='100500',
                                                     short_name='sis-100500',
                                                     is_public=True),
                        models.School.objects.create(name='ЛКШ 100501',
                                                     year='100501',
                                                     short_name='sis-100501',
                                                     is_public=False)]

    @unittest.mock.patch('schools.views.user')
    def test_index_for_student(self, user_view_mock):
        """Index returns correct page for student"""
        for school in self.schools:
            request = self.request_factory.get('/%s/' % school.short_name)
            request.user = self.student
            views.index(request, school.short_name)
            if school.is_public:
                user_view_mock.assert_called_once_with(request)
            else:
                user_view_mock.assert_not_called()
            self.assertEqual(request.school, school)
            user_view_mock.reset_mock()


    @unittest.mock.patch('schools.views.staff')
    def test_index_for_teacher(self, staff_view_mock):
        """Index returns correct page for teacher"""
        for school in self.schools:
            request = self.request_factory.get('/%s/' % school.short_name)
            request.user = self.teacher
            views.index(request, school.short_name)
            staff_view_mock.assert_called_with(request)
            self.assertEqual(request.school, school)
            staff_view_mock.reset_mock()

    @unittest.mock.patch('django.shortcuts.redirect')
    def test_staff(self, redirect_mock):
        """Staff view makes correct redirect"""
        for school in self.schools:
            request = self.request_factory.get('/%s/' % school.short_name)
            request.user = self.teacher
            request.school = school
            views.staff(request)
            redirect_mock.assert_called_once_with('school:entrance:enrolling',
                                                  school_name=school.short_name)
            redirect_mock.reset_mock()

    # TODO(Artem Tabolin): test the case with some blocks
    @unittest.mock.patch('django.shortcuts.render')
    def test_user_no_blocks(self, render_mock):
        """User view renders correct template with correct arguments"""
        school = self.schools[0]

        request = self.request_factory.get('/%s/' % school.short_name)
        request.user = self.student
        request.school = school
        views.user(request)
        render_mock.assert_called_once_with(
            request,
            'home/user.html',
            {'school': school, 'blocks': []})

