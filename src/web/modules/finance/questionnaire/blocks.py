import questionnaire.models

from ..models.payment_amount import PaymentAmount

from ..templatetags.money import money_russian_pluralize


class PaymentInfoQuestionnaireBlock(questionnaire.models.MarkdownQuestionnaireBlock):
    block_name = 'payment_info'

    def fill_for_user(self, user):
        school = self.questionnaire.school
        if school is None:
            raise ValueError('modules.finance.questionnaire.PaymentInfoQuestionnaireBlock can be ' +
                             'inserted only in school-related questionnaire')
        payment_amount, payment_currency = PaymentAmount.get_amount_for_user(school, user)

        if payment_amount is None:
            new_text = ''
        else:
            new_text = self.markdown.replace(
                '{{ payment_amount }}', money_russian_pluralize(payment_amount, payment_currency)
            )

        return questionnaire.models.MarkdownQuestionnaireBlock(markdown=new_text)
