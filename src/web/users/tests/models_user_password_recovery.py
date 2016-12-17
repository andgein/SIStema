import unittest

from django.test import TestCase
from users.models import User, UserPasswordRecovery

class UserPasswordRecoveryTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(
                username='test_user_1',
                email='semen@pechkin-lavochkin.org')

    def test_recovery_tokens_are_different(self):
        """Full name should consist of first and last names separated by a
        space.
        """
        user = User.objects.get(username='test_user_1')
        recovery1 = UserPasswordRecovery(user=user)
        recovery2 = UserPasswordRecovery(user=user)
        self.assertNotEqual(recovery1.recovery_token, recovery2.recovery_token)
