from modules.entrance import levels
from modules.topics import models


class TopicsEntranceLevelLimiter(levels.EntranceLevelLimiter):
    def __init__(self, school):
        super().__init__(school)
        self.questionnaire = self.school.topicquestionnaire
        if self.questionnaire is None:
            raise Exception(
                '{}.{}:cannot use TopicsEntranceLevelLimiter without topics '
                'questionnaire for this school'
                .format(self.__module__, self.__class__.__name__))

    def get_limit(self, user):
        return models.TopicsEntranceLevelLimit.get_limit(
            user=user, questionnaire=self.questionnaire)
