from django.template.loader import render_to_string

import home.models as home_models

__all__ = ['EntranceStepsHomePageBlock']


class EntranceStepsHomePageBlock(home_models.AbstractHomePageBlock):
    ENTRANCE_STEPS_TEMPLATES_FOLDER = 'entrance/steps'

    css_files = ['entrance/css/timeline.css']
    js_files = ['entrance/js/timeline.js']

    def build(self, request):
        # It's here to avoid cyclic imports
        from modules.entrance.models import steps as entrance_steps

        steps = entrance_steps.AbstractEntranceStep.objects.\
            filter(school=request.school)

        blocks = []
        for step in steps:
            block = step.build(request.user)

            if block is not None:
                # TODO(andgein): May be replace with {% include %} in template?
                template_file = '%s/%s' % (self.ENTRANCE_STEPS_TEMPLATES_FOLDER,
                                           step.template_file)
                rendered_block = render_to_string(template_file, {
                    'entrance_block': block,
                    'EntranceStepState': entrance_steps.EntranceStepState
                })

                blocks.append(rendered_block)

        self.blocks = blocks

# TODO (andgein): replace with the new Entrance Steps
"""
class EnrolledStepsHomePageBlock(home_models.AbstractHomePageBlock):
    def build(self, request):
        self.steps = None
        self.entrance_status = get_visible_entrance_status(request.school,
                                                           request.user)
        self.absence_reason = entrance_models.AbstractAbsenceReason.for_user_in_school(
            request.user, request.school)

        if self.entrance_status is not None and self.entrance_status.is_enrolled:
            user_session = self.entrance_status.session

            enrolled_questionnaire = questionnaire_models.Questionnaire.objects.filter(
                school=request.school, short_name='enrolled').first()
            arrival_questionnaire = questionnaire_models.Questionnaire.objects.filter(
                school=request.school,
                short_name__startswith='arrival',
                session=user_session
            ).first()
            payment_questionnaire = questionnaire_models.Questionnaire.objects.filter(
                school=request.school, short_name='payment').first()
            enrolled_steps = [
                (
                    'modules.entrance.steps.QuestionnaireEntranceStep', {
                        'school': request.school,
                        'questionnaire': enrolled_questionnaire,
                        'message': 'Подтвердите своё участие — заполните анкету зачисленного',
                        'button_text': 'Заполнить',
                    }
                ),
                (
                    'modules.entrance.steps.QuestionnaireEntranceStep', {
                        'school': request.school,
                        'questionnaire': arrival_questionnaire,
                        'previous_questionnaire': enrolled_questionnaire,
                        'message': 'Укажите информацию о приезде как только она станет известна',
                        'closed_message': 'Вносить изменения в анкету о приезде больше нельзя.',
                        'button_text': 'Заполнить',
                    }
                ),
                (
                    'modules.enrolled_scans.entrance.steps.EnrolledScansEntranceStep',
                    {
                        'school': request.school,
                        'previous_questionnaire': enrolled_questionnaire
                    }
                ),
                (
                    'modules.finance.entrance.steps.PaymentInfoEntranceStep', {
                        'school': request.school,
                        'payment_questionnaire': payment_questionnaire,
                        'previous_questionnaire': enrolled_questionnaire
                    }
                ),
                (
                    'modules.finance.entrance.steps.DocumentsEntranceStep', {
                        'school': request.school,
                        'payment_questionnaire': payment_questionnaire,
                    }
                ),
            ]

            # self.steps = build_user_steps(enrolled_steps, request.user)
            self.steps = []

class AbsenceReasonHomePageBlock(home_models.AbstractHomePageBlock):
    def build(self, request):
        self.reason = entrance_models.AbstractAbsenceReason.for_user_in_school(
            request.user, request.school)
"""