import importlib

from django.db import models

from ..models import main as entrance_models
import home.models as home_models
import questionnaire.models as q_models

__all__ = ['EntranceStepsHomePageBlock',
           'EnrolledStepsHomePageBlock',
           'EntranceStatusHomePageBlock',
           'AbsenceReasonHomePageBlock'
          ]


class UserStep:
    pass


def build_user_steps(steps, user):
    user_steps = []

    for class_name, params in steps:
        module_name, class_name = class_name.rsplit(".", 1)
        klass = getattr(importlib.import_module(module_name), class_name)
        step = klass(**params)

        rendered_step = step.render(user)
        # TODO: create custom model
        user_step = UserStep()
        user_step.is_available = step.is_available(user)
        user_step.is_passed = step.is_passed(user)
        user_step.rendered = rendered_step

        user_steps.append(user_step)

    return user_steps


def get_visible_entrance_status(school, user):
    qs = entrance_models.EntranceStatus.objects.filter(school=school, user=user, is_status_visible=True)
    entrance_status = None
    if qs.exists():
        entrance_status = qs.first()
        entrance_status.is_enrolled = entrance_status.status == entrance_models.EntranceStatus.Status.ENROLLED
    return entrance_status


class EntranceStepsHomePageBlock(home_models.AbstractHomePageBlock):
    is_past = models.BooleanField(default=False)

    def build(self, request):
        steps = [
            (
                'modules.entrance.steps.QuestionnaireEntranceStep', {
                    'school': request.school,
                    'questionnaire': q_models.Questionnaire.objects.filter(short_name='about').first()
                }
            ),
            (
                'modules.entrance.steps.QuestionnaireEntranceStep', {
                    'school': request.school,
                    'questionnaire': q_models.Questionnaire.objects.filter(school=request.school).first(),
                    'previous_questionnaire': q_models.Questionnaire.objects.filter(short_name='about').first(),
                    'message': 'Заполните анкету поступающего для {{ school.name }}',
                    'button_text': 'Поехали',
                }
            ),
            (
                'modules.topics.entrance.steps.TopicQuestionnaireEntranceStep', {
                    'school': request.school,
                    'questionnaire': request.school.topicquestionnaire,
                    'previous_questionnaire': q_models.Questionnaire.objects.filter(school=request.school).first(),
                }
            ),
            (
                'modules.entrance.steps.ExamEntranceStep', {
                    'school': request.school,
                    'previous_questionnaire': request.school.topicquestionnaire,
                }
            )
        ]

        self.steps = build_user_steps(steps, request.user)

    @property
    def columns_count(self):
        return 4 if self.is_past else 2

    @property
    def bootstrap_column_width(self):
        return 3 if self.is_past else 6


class EnrolledStepsHomePageBlock(home_models.AbstractHomePageBlock):
    def build(self, request):
        self.steps = None
        self.entrance_status = get_visible_entrance_status(request.school, request.user)
        self.absence_reason = entrance_models.AbstractAbsenceReason.for_user_in_school(request.user, request.school)

        if self.entrance_status is not None and self.entrance_status.is_enrolled:
            user_session = self.entrance_status.session

            enrolled_questionnaire = q_models.Questionnaire.objects.filter(school=request.school, short_name='enrolled').first()
            arrival_questionnaire = q_models.Questionnaire.objects.filter(
                school=request.school,
                short_name__startswith='arrival',
                session=user_session
            ).first()
            payment_questionnaire = q_models.Questionnaire.objects.filter(school=request.school, short_name='payment').first()
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
                    'modules.enrolled_scans.entrance.steps.EnrolledScansEntranceStep', {
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

            self.steps = build_user_steps(enrolled_steps, request.user)


class EntranceStatusHomePageBlock(home_models.AbstractHomePageBlock):
    def build(self, request):
        entrance_status = get_visible_entrance_status(request.school, request.user)
        if entrance_status is not None:
            if entrance_status.is_enrolled:
                entrance_status.message = 'Поздравляем! Вы приняты в %s, в параллель %s смены %s' % (
                    request.school.name, entrance_status.parallel.name, entrance_status.session.name
                )
            else:
                entrance_status.message = 'К сожалению, вы не приняты в %s' % (request.school.name,)
                if entrance_status.public_comment:
                    entrance_status.message += '.\nПричина: %s' % (entrance_status.public_comment,)

        self.entrance_status = entrance_status


class AbsenceReasonHomePageBlock(home_models.AbstractHomePageBlock):
    def build(self, request):
        self.reason = entrance_models.AbstractAbsenceReason.for_user_in_school(request.user, request.school)
