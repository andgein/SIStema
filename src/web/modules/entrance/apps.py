from django.apps import AppConfig
from . import groups


class EntranceConfig(AppConfig):
    name = 'modules.entrance'

    sistema_groups = {
        groups.ADMINS: {
            'name': 'Админы вступительной',
            'description': 'Группа администраторов вступительной работы',
        },
        groups.CAN_CHECK: {
            'name': 'Проверяющие вступительную',
            'description':
                'Группа пользователей, которые могут проверять вступительную '
                'работу: смотреть решения школьников, писать к ним комментарии '
                'и ставить за них баллы',
            'auto_members': [groups.ADMINS],
            'auto_access': {
                groups.ADMINS: 'admin',
            }
        },
        groups.ENROLLMENT_TYPE_REVIEWERS: {
            'name': 'Модераторы способов поступления',
            'description':
                'Группа пользователей, которые могут проверять и одобрять '
                'выбранные школьниками способы поступления',
            'auto_members': [groups.ADMINS],
            'auto_access': {
                groups.ADMINS: 'admin',
            }
        }
    }
