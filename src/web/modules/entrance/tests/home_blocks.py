"""Tests for modules.entrance.home.blocks."""

import django.test

from modules.entrance.home import blocks


class UserStepMock:
    def __init__(self, is_available, is_passed, render_result):
        self._is_available = is_available
        self._is_passed = is_passed
        self._render_result = render_result

    def is_available(self, user):
        return self._is_available

    def is_passed(self, user):
        return self._is_passed

    def render(self, user):
        return self._render_result


class HomeBlocksTestCase(django.test.TestCase):
    def test_build_user_steps_empty(self):
        """build_user_steps should return empty list for empty imput list."""
        self.assertEqual(blocks.build_user_steps([], None), [])

    def test_build_user_steps(self):
        """"build_user_steps should return a list of correct rendered user
        steps.
        """
        step_calls = [
            ('modules.entrance.tests.UserStepMock', {
                'is_available': False,
                'is_passed': False,
                'render_result': 'First step'}),
            ('modules.entrance.tests.UserStepMock', {
                'is_available': True,
                'is_passed': True,
                'render_result': 'Second step'})]

        # Passing None as user shouldn't be used in other way than passing
        # through to step class' __init__ method.
        user_steps = blocks.build_user_steps(step_calls, None)

        self.assertFalse(user_steps[0].is_available)
        self.assertFalse(user_steps[0].is_passed)
        self.assertEqual(user_steps[0].rendered, 'First step')

        self.assertTrue(user_steps[1].is_available)
        self.assertTrue(user_steps[1].is_passed)
        self.assertEqual(user_steps[1].rendered, 'Second step')
