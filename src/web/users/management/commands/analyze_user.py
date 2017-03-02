# -*- coding: utf-8 -*-

from django.core.management import base as management_base
from django.contrib.admin.utils import NestedObjects

from users import models


def analyze_all_related_objects(model, dumper=None):
    collector = NestedObjects(using="default")  # database name
    collector.collect([model])  # list of objects. single one won't do
    res = 0
    for obj_set in collector.data.values():
        res += len(obj_set)
        if dumper:
            dumper.write('\n'.join(map(str, obj_set)) + '\n')
    return res


class Command(management_base.BaseCommand):
    help = 'Analyze all objects related with user'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=int, help='search user by its id')
        parser.add_argument('--email', help='search user by its email')
        parser.add_argument('--username', help='search user by its username')
        parser.add_argument('--dump', action='store_true', help='dump all related objects')

    def handle(self, *args, **options):
        if options['user_id']:
            users = models.User.objects.filter(id=options['user_id'])
        elif options['email']:
            users = models.User.objects.filter(email=options['email'])
        elif options['username']:
            users = models.User.objects.filter(email=options['username'])
        else:
            raise Exception('It is required one of --user_id, --email or --username')

        dumper = self.stdout if options['dump'] else None

        self.stdout.write('Found %d users...\n' % len(users))
        for user in users:
            objects_count = analyze_all_related_objects(user, dumper)
            self.stdout.write("user_id %d username '%s' email '%s' objects %d\n"
                              % (user.id, user.username, user.email, objects_count))
