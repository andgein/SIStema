from django.db import models

import sistema.helpers
from questionnaire import models as questionnaire_models
from modules.entrance.models import steps
from modules.finance import models as finance_models


__all__ = ['FillPaymentInfoEntranceStep', 'DocumentsEntranceStep']


class FillPaymentInfoEntranceStep(steps.FillQuestionnaireEntranceStep):
    template_file = 'finance/fill_payment_info.html'

    def build(self, user):
        block = super().build(user)
        if block is not None:
            block.payment_amount = finance_models.PaymentAmount.get_amount_for_user(
                self.school, user
            )
            block.user_discounts = finance_models.Discount.objects.filter(
                school=self.school, user=user
            )
            block.actual_discounts = block.user_discounts.filter(amount__gt=0)
            block.considered_discounts = block.user_discounts.filter(amount=0)

        return block

    def __str__(self):
        return 'Шаг заполнения информации об оплате для ' + self.school.name


class DocumentsEntranceStep(steps.AbstractEntranceStep, steps.EntranceStepTextsMixIn):
    text_no_required_documents = models.TextField(
        help_text='Текст, который показывается, если школьнику '
                  'не нужны никакие документы. Поддерживается Markdown.',
        blank=True,
        default='',
    )

    document_types = models.ManyToManyField(
        finance_models.DocumentType,
        help_text='Документы, которые нужно сгенерировать на этом шаге',
        blank=True,
    )

    template_file = 'finance/documents.html'

    def is_passed(self, user):
        return False

    def build(self, user):
        block = super().build(user)

        document_types = self._get_needed_document_types(user)
        block.documents = []
        if len(document_types) == 0:
            return block

        has_ready_document = False
        for document_type in document_types:
            not_answered_questions = self._get_not_answered_questions(user, document_type)
            is_ready = len(not_answered_questions) == 0

            block.documents.append({
                'document_type': document_type,
                'is_ready': is_ready,
                'not_answered_questions': not_answered_questions,
            })
            has_ready_document = has_ready_document or is_ready

        return block

    def _get_needed_document_types(self, user):
        document_types = self.document_types.all()

        needed_documents = []
        for document_type in document_types:
            if document_type.is_need_for_user(user):
                needed_documents.append(document_type)
        return needed_documents

    @staticmethod
    def _get_not_answered_questions(user, document_type):
        required_questions = list(document_type.required_questions.all())
        required_questions_questionnaires_ids = {
            q.questionnaire_id for q in required_questions
        }

        user_answers = questionnaire_models.QuestionnaireAnswer.objects.filter(
            questionnaire_id__in=required_questions_questionnaires_ids,
            question_short_name__in=[q.short_name for q in required_questions],
            user=user,
        ).exclude(answer='')

        user_answers = sistema.helpers.group_by(
            user_answers,
            lambda answer: (answer.questionnaire_id, answer.question_short_name)
        )

        not_answered_questions = []
        for question in required_questions:
            if (question.questionnaire_id, question.short_name) not in user_answers:
                not_answered_questions.append(question)

        return [question.text for question in not_answered_questions]
