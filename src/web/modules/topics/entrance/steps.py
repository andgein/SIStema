from django.db import models, IntegrityError
from django.db.models.signals import pre_save

import modules.entrance.models.steps as entrance_steps


class FillTopicsQuestionnaireEntranceStep(
        entrance_steps.AbstractEntranceStep,
        entrance_steps.EntranceStepTextsMixIn):
    template_file = 'topics/fill_topics_questionnaire.html'

    questionnaire = models.ForeignKey(
        'topics.TopicQuestionnaire',
        on_delete=models.CASCADE,
        help_text='Тематическая анкета, которую нужно заполнить',
        related_name='+'
    )

    text_questionnaire_not_finished = models.TextField(
        help_text='Текст, который показывается, когда анкета недозаполнена. '
                  'Поддерживается Markdown',
        blank=True
    )

    text_questionnaire_correcting = models.TextField(
        help_text='Текст, который показывается, когда пользователь '
                  'не подтвердил оценки. Поддерживается Markdown',
        blank=True
    )

    text_questionnaire_is_on_checking_questions = models.TextField(
        help_text='Текст, который показывается, когда пользователь '
                  'не ответил на проверочные вопросы. Поддерживается Markdown',
        blank=True
    )

    @classmethod
    def pre_save(cls, instance, **kwargs):
        if (instance.questionnaire_id is not None and
               instance.questionnaire.school is not None and
               instance.school_id != instance.questionnaire.school_id):
            raise IntegrityError(
                "{}.{}: questionnaire should belong to the step's school"
                .format(cls.__module__, cls.__name__))

    def is_passed(self, user):
        return super().is_passed(user) and self.questionnaire.is_filled_by(user)

    def build(self, user):
        # It's here to avoid cyclic imports
        import modules.topics.models.main as topics_models

        block = super().build(user)
        if block is not None:
            block.questionnaire_status = self.questionnaire.get_status(user)
            block.UserQuestionnaireStatus = \
                topics_models.UserQuestionnaireStatus.Status
        return block

    def __str__(self):
        return ('Шаг заполнения тематической анкеты %s' %
               (str(self.questionnaire), ))


pre_save.connect(
    FillTopicsQuestionnaireEntranceStep.pre_save,
    sender=FillTopicsQuestionnaireEntranceStep,
)
