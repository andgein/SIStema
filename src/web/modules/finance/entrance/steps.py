from django.db import models

import sistema.helpers
from modules.entrance.models import steps
from modules.finance import models as finance_models
import questionnaire.models

__all__ = ['FillPaymentInfoEntranceStep', 'DocumentsEntranceStep']


class FillPaymentInfoEntranceStep(steps.FillQuestionnaireEntranceStep):
    template_file = 'finance/fill_payment_info.html'

    def build(self, user):
        block = super().build(user)
        if block is not None:
            block.payment_amount, block.payment_currency = (
                finance_models.PaymentAmount.get_amount_for_user(self.school, user)
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
    )

    document_types = models.ManyToManyField(
        finance_models.DocumentType,
        help_text='Документы, которые нужно сгенерировать на этом шаге',
        blank=True,
    )

    def __str__(self):
        return 'Шаг скачивания документов для %s' % self.school

    template_file = 'finance/documents.html'

    def is_passed(self, user):
        return False

    def build(self, user):
        block = super().build(user)

        document_types = self._get_needed_document_types(user)
        block.documents = []
        if not document_types:
            return block

        for document_type in document_types:
            unanswered_questions = self._get_unanswered_questions(user, document_type)
            is_ready = not unanswered_questions

            block.documents.append({
                'document_type': document_type,
                'is_ready': is_ready,
                'unanswered_questions': unanswered_questions,
            })

        return block

    def _get_needed_document_types(self, user):
        document_types = self.document_types.all()

        needed_document_types = []
        for document_type in document_types:
            if document_type.is_need_for_user(user):
                needed_document_types.append(document_type)
        return needed_document_types

    @staticmethod
    def _get_unanswered_questions(user, document_type):
        required_questions = document_type.required_questions.all()
        required_questions_questionnaire_ids = {
            q.questionnaire_id for q in required_questions
        }

        # Collect non empty user answers for required questions.
        # Some other answers may be collected (i.e. with the same short_name
        # in other questionnaire).
        # It's the easiest way to select all needed answers in one query
        user_answers = questionnaire.models.QuestionnaireAnswer.objects.filter(
            questionnaire_id__in=required_questions_questionnaire_ids,
            question_short_name__in=[q.short_name for q in required_questions],
            user=user,
        ).exclude(answer='')

        # Group answers by (questionnaire_id, question_short_name). This pair
        # defines question uniquely
        user_answers = sistema.helpers.group_by(
            user_answers,
            lambda answer: (answer.questionnaire_id, answer.question_short_name)
        )

        # Find required questions which are not in the answers list
        unanswered_questions = []
        for question in required_questions:
            if (question.questionnaire_id, question.short_name) not in user_answers:
                unanswered_questions.append(question)

        return unanswered_questions
