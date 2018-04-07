from django.db import models, IntegrityError

import groups.models
from questionnaire.models import Questionnaire


class UsersFilledQuestionnaireGroup(groups.models.AbstractGroup):
    questionnaire = models.ForeignKey(
        Questionnaire,
        help_text='В группу автоматически попадут все пользователи, заполнившие эту анкету',
        on_delete=models.CASCADE,
        related_name='+',
    )

    @property
    def user_ids(self):
        return self.questionnaire.get_filled_user_ids()


class UsersNotFilledQuestionnaireGroup(groups.models.AbstractGroup):
    questionnaire = models.ForeignKey(
        Questionnaire,
        help_text='В группу автоматически попадут все пользователи, НЕ заполнившие эту анкету. '
                  'Для анкеты должно быть установлено поле must_fill',
        on_delete=models.CASCADE,
        related_name='+',
    )

    def save(self, *args, **kwargs):
        if self.questionnaire.must_fill is None:
            raise IntegrityError('Questionnaire should have not-null field must_fill')
        super().save(*args, **kwargs)

    @property
    def user_ids(self):
        filled_users_ids = set(self.questionnaire.get_filled_user_ids())
        must_fill_users_ids = set(self.questionnaire.must_fill.user_ids)
        return must_fill_users_ids - filled_users_ids
