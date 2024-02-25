"""Tests for entrance levels"""

from django.test import TransactionTestCase

import schools.models
import users.models
from modules.entrance import models
from modules.entrance.models import levels


class AlreadyWasEntranceLevelLimiterTestCase(TransactionTestCase):
    fixtures = ['schools-test-sample-schools']

    def setUp(self):
        # Schools
        self.prev_school_1 = schools.models.School.objects.get(pk=1)
        self.prev_school_2 = schools.models.School.objects.get(pk=2)
        self.school = schools.models.School.objects.get(pk=3)

        # Parallels
        self.s1_c_prime = schools.models.Parallel.objects.create(
            school=self.prev_school_1,
            short_name='c_prime',
            name="C'",
        )
        self.s1_b = schools.models.Parallel.objects.create(
            school=self.prev_school_1,
            short_name='b',
            name="B",
        )
        self.s1_as = schools.models.Parallel.objects.create(
            school=self.prev_school_1,
            short_name='as',
            name="AS",
        )
        self.s2_c_cpp = schools.models.Parallel.objects.create(
            school=self.prev_school_2,
            short_name='c.cpp',
            name="C.C++",
        )
        self.s2_c_py = schools.models.Parallel.objects.create(
            school=self.prev_school_2,
            short_name='c.python',
            name="C.python",
        )
        self.s2_p = schools.models.Parallel.objects.create(
            school=self.prev_school_2,
            short_name='p',
            name="P",
        )

        # Levels
        self.c_prime = models.EntranceLevel.objects.create(
            school=self.school,
            short_name='c_prime',
            name="C'",
            order=10,
        )
        self.c = models.EntranceLevel.objects.create(
            school=self.school,
            short_name='c',
            name="C'-C",
            order=20,
        )
        self.b_prime = models.EntranceLevel.objects.create(
            school=self.school,
            short_name='b_prime',
            name="C-B'",
            order=30,
        )
        self.b = models.EntranceLevel.objects.create(
            school=self.school,
            short_name='b',
            name="B'-B",
            order=40,
        )
        self.a_prime = models.EntranceLevel.objects.create(
            school=self.school,
            short_name='a_prime',
            name="B-A'",
            order=50,
        )
        self.a = models.EntranceLevel.objects.create(
            school=self.school,
            short_name='a',
            name="A'-A",
            order=60,
        )

        self.limiter = levels.AlreadyWasEntranceLevelLimiter.objects.create(school=self.school)
        levels.AlreadyWasEntranceLevelLimiterForParallel.objects.create(
            limiter=self.limiter,
            previous_parallel_short_name='c_prime',
            level=self.c
        )
        levels.AlreadyWasEntranceLevelLimiterForParallel.objects.create(
            limiter=self.limiter,
            previous_parallel=self.s2_c_py,
            level=self.b_prime
        )
        levels.AlreadyWasEntranceLevelLimiterForParallel.objects.create(
            limiter=self.limiter,
            previous_parallel_short_name='b_prime',
            level=self.b
        )
        levels.AlreadyWasEntranceLevelLimiterForParallel.objects.create(
            limiter=self.limiter,
            previous_parallel_short_name='b',
            level=self.a_prime
        )

    def test_no_participations(self):
        """
        The lowest limit is returned for a user with no school participations
        """
        user = users.models.User.objects.create_user('test-user')
        limit = self.limiter.get_limit(user)
        self.assertEqual(limit.min_level, self.c_prime)

    def test_one_participation(self):
        """
        User cannot study in the same or lower parallel after single
        participation.
        """
        user = users.models.User.objects.create_user('test-user')
        user.school_participations.create(
            school=self.prev_school_1, parallel=self.s1_b)
        limit = self.limiter.get_limit(user)
        self.assertEqual(limit.min_level, self.a_prime)

    def test_two_participations(self):
        """
        User cannot study in the same or lower parallel after several
        participations
        """
        user = users.models.User.objects.create_user('test-user')
        user.school_participations.create(
            school=self.prev_school_1, parallel=self.s1_c_prime)
        user.school_participations.create(
            school=self.prev_school_2, parallel=self.s2_c_py)
        limit = self.limiter.get_limit(user)
        self.assertEqual(limit.min_level, self.b_prime)

    def test_non_algorithmic(self):
        """
        Non-algorithmic parallels don't influence limiter
        """
        user = users.models.User.objects.create_user('test-user')
        user.school_participations.create(
            school=self.prev_school_1, parallel=self.s1_c_prime)
        user.school_participations.create(
            school=self.prev_school_2, parallel=self.s2_p)
        limit = self.limiter.get_limit(user)
        self.assertEqual(limit.min_level, self.c)
