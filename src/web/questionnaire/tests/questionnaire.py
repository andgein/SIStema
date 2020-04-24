"""Tests for questionnaire.Questionnaire, including blocks and questions"""

import datetime

import django.test
from django.db import IntegrityError

from dates.models import KeyDate
from questionnaire import models
from schools.models import School, Session


class QuestionnaireTestCase(django.test.TestCase):
    def setUp(self):
        self.school_1 = School.objects.create(
            name="Test school 1",
            year='2048',
            short_name='school-1',
        )
        self.session_1 = Session.objects.create(
            school=self.school_1,
            name="Session 1",
            short_name='session-1',
            start_date=datetime.datetime(2048, 7, 1),
            finish_date=datetime.datetime(2048, 8, 1),
        )

        self.school_2 = School.objects.create(
            name="Test school 2",
            year='4096',
            short_name='school-2',
        )
        self.session_2 = Session.objects.create(
            school=self.school_2,
            name="Session 2",
            short_name='session-2',
            start_date=datetime.datetime(4096, 7, 1),
            finish_date=datetime.datetime(4096, 8, 1),
        )

        self.close_date = KeyDate.objects.create(
            datetime=datetime.datetime(2048, 3, 1),
        )

        self.src_q = models.Questionnaire.objects.create(
            title='Test questionnaire',
            short_name='test-questionnaire',
            school=self.school_1,
            session=self.session_1,
            close_time=self.close_date,
        )

    def test_clone_empty(self):
        """Empty questionnaire is correctly cloned"""
        # Either questionnaire's school or short_names should be changed.
        # Otherwise copy should fail due to the unique constraint.
        with self.assertRaises(IntegrityError):
            self.src_q.clone()

        # Copy to another school
        dst_q = self.src_q.clone(new_school=self.school_2)
        self.assertEqual(dst_q.title, self.src_q.title)
        self.assertEqual(dst_q.short_name, self.src_q.short_name)
        self.assertEqual(dst_q.school, self.school_2)
        self.assertIsNone(dst_q.session)
        self.assertIsNone(dst_q.close_time)

        # Copy within the school
        dst_q = self.src_q.clone(new_short_name='dst-q')
        self.assertEqual(dst_q.title, self.src_q.title)
        self.assertEqual(dst_q.short_name, 'dst-q')
        self.assertEqual(dst_q.school, self.school_1)
        self.assertEqual(dst_q.session, self.src_q.session)
        self.assertEqual(dst_q.close_time, self.src_q.close_time)

        # Copy with changing everything
        dst_close_time = KeyDate.objects.create(
            datetime=datetime.datetime(2048, 4, 1),
        )
        dst_q = self.src_q.clone(
            new_school=self.school_2,
            new_short_name='dst-q-2',
            new_session=self.session_2,
            new_close_time=dst_close_time,
        )
        self.assertEqual(dst_q.short_name, 'dst-q-2')
        self.assertEqual(dst_q.school, self.school_2)
        self.assertEqual(dst_q.session, self.session_2)
        self.assertEqual(dst_q.close_time, dst_close_time)

        # Catch not matching session and school
        with self.assertRaises(IntegrityError):
            self.src_q.clone(
                new_school=self.school_2, new_session=self.session_1,
                new_short_name='dst-q-3'
            )

