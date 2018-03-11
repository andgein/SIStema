"""Tests for questionnaire blocks"""

from unittest import mock

import django.test

from questionnaire import models
from sistema.polymorphic import get_all_inheritors


class QuestionnaireBlocksTestCase(django.test.TestCase):

    @mock.patch.object(models.AbstractQuestionnaireBlock,
                       '_copy_fields_to_instance')
    @mock.patch.object(models.AbstractQuestionnaireBlock,
                       '_copy_dependencies_to_instance')
    def test_copy_method_overrides_call_super(
            self, copy_deps_mock, copy_fields_mock):
        """
        Check that overrides for `_copy_fields_to_instance` and
        `_copy_dependencies_to_instance` call super methods
        """
        block_classes = get_all_inheritors(models.AbstractQuestionnaireBlock)
        for klass in block_classes:
            instance = klass()

            copy_fields_mock.reset_mock()
            instance._copy_fields_to_instance(object())
            self.assertEqual(
                copy_fields_mock.call_count,
                1,
                "{}._copy_fields_to_instance doesn't call super()".format(
                    klass.__name__))

            copy_deps_mock.reset_mock()
            instance._copy_dependencies_to_instance(object())
            self.assertEqual(
                copy_deps_mock.call_count,
                1,
                "{}._copy_dependencies_to_instance doesn't call super()".format(
                    klass.__name__))
