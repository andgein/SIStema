from django.apps import AppConfig
from . import groups


class StudyResultsConfig(AppConfig):
    name = 'modules.study_results'

    sistema_groups = {
        groups.STUDENT_COMMENTS_VIEWERS: {
            'name': 'Имеющие доступ к комментариям о школьниках',
            'description': 'Группа пользователей, имеющих доступ к просмотру '
                           'комментариев о школьниках',
        },
        groups.STUDENT_COMMENTS_EDITORS: {
            'name': 'Имеющие право редактировать комментарии о школьниках',
            'description': 'Группа пользователей, которые могут редактировать '
                           'комментарии о школьниках'
        }
    }
