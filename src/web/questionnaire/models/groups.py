from django.db import models

import groups.models
from questionnaire.models import Questionnaire


class UsersFilledQuestionnaireGroup(groups.models.AbstractGroup):
    questionnaire = models.ForeignKey(
        Questionnaire,
        help_text='Анкета, заполнившие которую пользователи автоматически попадут в эту группу',
        on_delete=models.CASCADE,
        related_name='+',
    )

    @property
    def users_ids(self):
        return self.questionnaire.get_filled_users_ids()


class UsersNotFilledQuestionnaireGroup(groups.models.AbstractGroup):
    questionnaire = models.ForeignKey(
        Questionnaire,
        help_text='Анкета, незаполнившие которую пользователи автоматически попадут в эту группу. '
                  'Для анкеты должно быть установлено поле must_fill',
        on_delete=models.CASCADE,
        related_name='+',
    )

    def save(self, *args, **kwargs):
        if self.questionnaire.must_fill is None:
            raise ValueError('Questionnaire should has not-null field must_fill')
        super().save(*args, **kwargs)

    @property
    def users_ids(self):
        filled_users_ids = set(self.questionnaire.get_filled_users_ids())
        must_fill_users_ids = set(self.questionnaire.must_fill.users_ids)
        return must_fill_users_ids - filled_users_ids
