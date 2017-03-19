from modules.entrance.models import steps
from modules.finance import models


class FillPaymentInfoEntranceStep(steps.FillQuestionnaireEntranceStep):
    template_file = 'finance/fill_payment_info.html'

    def build(self, user):
        block = super().build(user)
        if block is not None:
            block.payment_amount = models.PaymentAmount.get_amount_for_user(
                self.school, user
            )
            block.user_discounts = models.Discount.objects.filter(
                school=self.school, user=user
            )
            block.actual_discounts = block.user_discounts.filter(amount__gt=0)
            block.considered_discounts = block.user_discounts.filter(amount=0)

        return block

    def __str__(self):
        return 'Шаг заполнения информации об оплате для ' + self.school.name

# TODO (andgein): Replace with the new entrance step
"""
class DocumentsEntranceStep(steps.EntranceStep):
    def __init__(self, school, payment_questionnaire):
        super().__init__(school, previous_questionnaire=payment_questionnaire)
        self.payment_questionnaire = payment_questionnaire
        if self.payment_questionnaire.school_id != self.school.id:
            raise ValueError(
                'finance.entrance.steps.DocumentsEntranceStep: '
                'PaymentQuestionnaire must be for this school')

    def _get_needed_document_types(self, user):
        document_types = models.DocumentType.objects.filter(school=self.school)

        needed_documents = []
        for document_type in document_types:
            if document_type.is_need_for_user(user):
                needed_documents.append(document_type)
        return needed_documents

    # TODO: this should be implemented via required fields in questionnaire with show conditions
    @staticmethod
    def _get_required_payment_questionnaire_fields(document_type):
        if document_type.short_name in ['contract_nccnse', 'contract_bp', 'instructions_nccnse']:
            return ['billing_person_name',
                    'billing_person_sex',
                    'billing_person_passport',
                    'billing_person_passport_issuer',
                    'billing_person_passport_unit_code',
                    'billing_person_passport_issue_date',
                    'billing_person_address',
                    'billing_person_phone'
                    ]
        return []

    def _get_not_filled_required_payment_questionnaire_fields(self, user, document_type):
        required_fields = self._get_required_payment_questionnaire_fields(document_type)
        required_fields_full_names = {
            q.short_name: q.text for q in
            questionnaire.models.AbstractQuestionnaireQuestion.objects.filter(
                questionnaire=self.payment_questionnaire,
                short_name__in=required_fields
            )
        }

        # TODO: set ForeignKey's related_name and replace with self.payment_questionnaire.answers
        user_payment_questionnaire = questionnaire.models.QuestionnaireAnswer.objects.filter(
            questionnaire=self.payment_questionnaire,
            user=user
        )
        answered_questions = {a.question_short_name for a in user_payment_questionnaire if a.answer != ''}

        not_filled_fields = []
        for required_field in required_fields:
            if required_field not in answered_questions:
                not_filled_fields.append(required_field)

        return list(filter(bool,
                           [required_fields_full_names.get(field, None) for field in not_filled_fields]
                           ))

    def render(self, user):
        if not self.is_available(user):
            template = self._template_factory('''
            <p>
                После заполнения информации об оплате здесь можно будет скачать договор и акт.
            </p>
            ''')
            body = template.render()
            return self.panel('Документы', body, 'default')

        document_types = self._get_needed_document_types(user)

        if len(document_types) == 0:
            template = self._template_factory('''
                <p>
                    Если вы выбрали оплату наличными в первый день лагеря и указали, что договор и акт не нужны, то
                    пока по оплате от вас больше ничего не требуется.
                </p>
                <p>
                    Если вы указали, что оргвзнос за вас оплачивает организация, то напишите нам на
                    <a href="mailto:oplata@lksh.ru">oplata@lksh.ru</a> — мы вышлем все необходимые документы.
                </p>
                ''')
            body = template.render()
            return self.panel('Документы', body, 'success')

        body = ''
        has_ready_document = False
        for document_type in document_types:
            not_filled_fields = self._get_not_filled_required_payment_questionnaire_fields(user, document_type)
            if not not_filled_fields:
                has_ready_document = True
                template = self._template_factory('''
                    {% load stringcase %}

                    <p>
                        Вы можете скачать подготовленный для вас
                        <a href="{% url 'school:finance:download' school.short_name document_type.short_name%}"><b>{{ document_type.name|lowerfirst }}</b></a>.
                        {% if document_type.additional_information %}
                            {{ document_type.additional_information }}
                        {% endif %}
                    </p>
                    ''')
                body += template.render({
                    'school': self.school,
                    'document_type': document_type,
                })
            else:
                template = self._template_factory('''
                    {% load stringcase %}

                    <p>
                        Чтобы скачать <b>{{ document_type.name|lowerfirst }}</b> укажите в
                        <a href="{% url 'school:questionnaire' school.short_name payment_questionnaire.short_name %}">информации об оплате</a>
                        {% for field in not_filled_fields %}<!--
                         -->{% if not forloop.last and not forloop.first %},{% elif not forloop.first %} и {% endif %}
                            {{ field|lowerfirst }}{% if forloop.last %}.{% endif %}<!--
                     -->{% endfor %}
                    </p>
                    ''')
                body += template.render({
                    'school': self.school,
                    'payment_questionnaire': self.payment_questionnaire,
                    'document_type': document_type,
                    'not_filled_fields': not_filled_fields
                })

        return self.panel(
            'Документы',
            body,
            'alert' if has_ready_document else 'danger'
        )

"""