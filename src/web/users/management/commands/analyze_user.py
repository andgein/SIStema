# -*- coding: utf-8 -*-

from django.core.management import base as management_base
from django.contrib.admin.utils import NestedObjects

from users import models


def find_all_related_objects(model):
    collector = NestedObjects(using="default")  # database name
    collector.collect([model])  # list of objects. single one won't do
    list = []
    for obj_set in collector.data.values():
        list += obj_set
    return list


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
            users = models.User.objects.filter(username=options['username'])
        else:
            raise Exception('It is required one of --user_id, --email or --username')

        dumper = self.stdout if options['dump'] else None

        self.stdout.write('Found %d users...\n' % len(users))
        for user in users:
            objects = find_all_related_objects(user)
            self.stdout.write("user_id %d username '%s' email '%s' objects %d\n"
                              % (user.id, user.username, user.email, len(objects)))
            if dumper:
                dumper.write('\n'.join(map(lambda x: x.__class__.__name__ + ": " + str(x), objects)) + '\n')

