from modules.entrance.models import levels
from modules.topics import models


class TopicsEntranceLevelLimiter(levels.EntranceLevelLimiter):
    def __str__(self):
        return "Лимитер по тематической анкете"

    def get_limit(self, user):
        questionnaire = self.school.topicquestionnaire
        if questionnaire is None:
            raise Exception(
                '{}.{}:cannot use TopicsEntranceLevelLimiter without topics '
                'questionnaire for this school'
                    .format(self.__module__, self.__class__.__name__))

        return models.TopicsEntranceLevelLimit.get_limit(
            user=user, questionnaire=questionnaire)
