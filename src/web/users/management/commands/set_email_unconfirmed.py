# -*- coding: utf-8 -*-

from django.core.management import base as management_base

from users import models


class Command(management_base.BaseCommand):
    help = 'Set user.is_email_confirmed=False for all user in range [from_user_id, user_id]'

    def add_arguments(self, parser):
        parser.add_argument('--from_user_id', type=int, help='left bound of range')
        parser.add_argument('--to_user_id', type=int, help='right bound of range')

    def handle(self, *args, **options):
        if options['from_user_id'] and options['to_user_id']:
            left_bound = options['from_user_id']
            right_bound = options['to_user_id']
        else:
            raise Exception('missing argument --from_user_id or --to_user_id')

        users = models.User.objects.filter(id__gte=left_bound, id__lte=right_bound)
        self.stdout.write('Found %d users...\n' % len(users))
        users.update(is_email_confirmed=False)
