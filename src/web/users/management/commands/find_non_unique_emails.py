# -*- coding: utf-8 -*-

from django.core.management import base as management_base

from users import models
from sistema import helpers

from users.management.commands import analyze_user


class Command(management_base.BaseCommand):
    help = 'Found not unique by ignore_case-equality emails'

    def handle(self, *args, **options):
        groups = helpers.group_by(models.User.objects.all(), lambda u: u.email.lower())
        for (key, users) in groups.items():
            results = map(lambda u: "%s %s %d" % (u.username, u.email, analyze_user.analyze_all_related_objects(u)),
                          users)
            if key == "":
                self.stdout.write('Found %d users with empty email\n' % len(users))
                self.stdout.write('\n'.join(results) + '\n')
            elif len(users) <= 1:
                pass
            elif len(users) == 2 and users[0].email == users[1].email:
                self.stdout.write('double register : %s\n' % ','.join(results))
            else:
                self.stdout.write("dup email %d : %s\n" % (len(users), ','.join(results)))
