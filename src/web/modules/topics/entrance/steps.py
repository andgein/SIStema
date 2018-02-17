from django.db import models

import modules.entrance.models.steps as entrance_steps


class FillTopicsQuestionnaireEntranceStep(entrance_steps.AbstractEntranceStep,
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

    def save(self, *args, **kwargs):
        if (self.questionnaire_id is not None and
           self.questionnaire.school is not None and
           self.school_id != self.questionnaire.school_id):
            raise ValueError(
                'topics.entrance.steps.FillTopicsQuestionnaireEntranceStep: '
                'questionnaire should belong to step\'s school')
        super().save(*args, **kwargs)

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
