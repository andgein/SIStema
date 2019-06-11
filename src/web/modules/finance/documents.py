import datetime

import generator.models
import questionnaire.models
from generator import generator
from modules.entrance.models import EntranceStatus
from . import models


class DocumentGenerator:
    def __init__(self, school):
        self.school = school
        self.payment_questionnaire = questionnaire.models.Questionnaire.objects.filter(
            school=self.school,
            short_name='payment'
        ).first()

        # TODO (andgein): This code should not contain questionnaire short_name
        if self.payment_questionnaire is None:
            self.payment_questionnaire = questionnaire.models.Questionnaire.objects.filter(
                school=self.school,
                short_name__in=['parent', 'details']
            ).first()

    def generate(self, document_type, user):
        if not self.payment_questionnaire.is_filled_by(user):
            raise ValueError('User has not fill the payment questionnaire')

        user_payment_questionnaire = self.payment_questionnaire.get_user_answers(
            user, substitute_choice_variants=True
        )

        # Some question may have several answers (i.e. multiple ChoiceQuestionnaireQuestion).
        # Join them by ', '.
        for question_short_name, answer in user_payment_questionnaire.items():
            if type(answer) is list:
                user_payment_questionnaire[question_short_name] = ', '.join(map(str, answer))

        entrance_status = EntranceStatus.get_visible_status(self.school, user)
        if entrance_status is None or entrance_status.status != EntranceStatus.Status.ENROLLED:
            raise ValueError('User has not enrolled')

        session_and_parallel = entrance_status.sessions_and_parallels.filter(selected_by_user=True).first()
        if session_and_parallel is None:
            raise ValueError('User did not select session for him')
        session = session_and_parallel.session

        price, currency = models.PaymentAmount.get_amount_for_user(self.school, user)

        g = generator.TemplateGenerator(document_type.template)
        return g.generate({
            'school': self.school,
            'session': session,
            'student': user.profile,
            'contract': {
                'id': user.id,
                'created_at': datetime.date.today()
            },
            'payment': user_payment_questionnaire,
            'price': price,
            'currency': currency,
        })
