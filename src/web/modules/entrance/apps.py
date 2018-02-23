from django.apps import AppConfig
from . import groups


class EntranceConfig(AppConfig):
    name = 'modules.entrance'

    sistema_groups = {
        groups.admins: {
            'name': 'Админы вступительной',
            'description': 'Группа администраторов вступительной работы',
        },
        groups.can_check: {
            'name': 'Проверяющие вступительную',
            'description': 'Группа пользователей, '
                           'которые могут проверять вступительную работу: '
                           'смотреть решения школьников, писать к ним комментарии и '
                           'ставить за них баллы',
            'auto_members': [groups.admins],
            'auto_access': {
                groups.admins: 'admin',
            }
        },
    }
