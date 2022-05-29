from modules.entrance.models import levels
from modules.topics import models


class TopicsEntranceLevelLimiter(levels.EntranceLevelLimiter):
    def __str__(self):
        return "Лимитер по тематической анкете"

    def get_limit(self, user):
        if not hasattr(self.school, 'topicquestionnaire'):
            raise Exception(
                '{}.{}:cannot use TopicsEntranceLevelLimiter without topics '
                'questionnaire for this school'
                    .format(self.__module__, self.__class__.__name__))

        questionnaire = self.school.topicquestionnaire

        return models.TopicsEntranceLevelLimit.get_limit(
            user=user, questionnaire=questionnaire)
