# -*- coding: utf-8 -*-

from django.core.management import base as management_base

from users import models
from sistema import helpers

from django import apps

from users import models as user_models
from modules.entrance import models as entrance_models
from users.management.commands import analyze_user

import operator
import uuid
import enum


def confirm_action(question):
    s = input("%s? y/n\n" % question)
    return s == 'y' or s == 'yes'


def import_class(full_class_name):
    import importlib
    (module_name, class_name) = full_class_name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


_empty_types = [user_models.User]
if apps.apps.is_installed('social_django'):
    _empty_types += [import_class('social_django.models.UserSocialAuth')]
if apps.apps.is_installed('allauth.account'):
    _empty_types += [import_class('allauth.account.models.EmailAddress')]
if apps.apps.is_installed('allauth.socialaccount'):
    _empty_types += [import_class('allauth.socialaccount.models.SocialAccount'),
                     import_class('allauth.socialaccount.models.SocialToken')]


def _is_empty_account(objects):
    for obj in objects:
        ok = False
        for _type in _empty_types:
            if isinstance(obj, _type):
                ok = True
                break
        if not ok:
            return False
    return True


class AccountInfo(object):
    class Status(enum.Enum):
        EMPTY = 0
        NO_ENTRANCE_STATUS = 1
        NOT_ENROLLED = 2
        ENROLLED = 3

        def __str__(self):
            text = ["EMPTY", "NO_ENTRANCE STATUS", "NOT_ENROLLED", "ENROLLED"]
            return text[self.value]

    def __init__(self, status, related_objects_count, user):
        self.status = status
        self.related_objects_count = related_objects_count
        self.user = user

    def __lt__(self, other):
        if self.status != other.status:
            return self.status.value < other.status.value
        if self.related_objects_count != other.related_objects_count:
            return self.related_objects_count < other.related_objects_count
        return self.user.id < other.user.id

    def __str__(self):
        return "%s obj_cnt %d user.id %d %s" % (
            str(self.status), self.related_objects_count, self.user.id, str(self.user)
        )

    @classmethod
    def build_for_user(cls, user):
        related_objects = analyze_user.find_all_related_objects(user)
        if _is_empty_account(related_objects):
            status = AccountInfo.Status.EMPTY
        else:
            entr_stat = [obj for obj in related_objects if isinstance(obj, entrance_models.EntranceStatus)]
            if len(entr_stat) > 2:
                raise Exception('Too many entrance statuses')
            if len(entr_stat) == 0:
                status = AccountInfo.Status.NO_ENTRANCE_STATUS
            # TODO (andgein): replace with not entr_stat[0].is_enrolled
            elif entr_stat[0].status != entrance_models.EntranceStatus.Status.ENROLLED:
                status = AccountInfo.Status.NOT_ENROLLED
            else:
                status = AccountInfo.Status.ENROLLED
        return AccountInfo(status, len(related_objects), user)


class Command(management_base.BaseCommand):
    help = 'Found not unique by ignore_case-equality emails'

    _to_deactivate_users = []
    _bad_users = []
    _bad_staff_users = []
    _apply_changes = False

    def add_arguments(self, parser):
        parser.add_argument('--apply-changes', action='store_true', help='apply changes in database')

    def handle(self, *args, **options):
        if 'apply_changes' in options:
            self._apply_changes = options['apply_changes']
        groups = helpers.group_by(models.User.objects.filter(is_active=True).all(),
                                  lambda u: u.email.lower())
        for (key, users) in groups.items():
            if key == "":
                for user in users:
                    self._process_empty_email_user(user)
            elif len(users) <= 1:
                pass
            else:
                self._process_duplicated_emails(users)
        self.stdout.write('Need to deactivate %d users...\n' % len(self._to_deactivate_users))
        self.stdout.write('Bad staff accounts: %d\n' % len(self._bad_staff_users))
        self.stdout.write('Bad accounts: %d\n' % len(self._bad_users))
        for user in self._to_deactivate_users:
            self._deactivate_user(user)
        for user in self._bad_users:
            account_info = AccountInfo.build_for_user(user)
            self.stdout.write('bad_user:\n%s\n' % str(account_info))
            candidates_users = user_models.User.objects.filter(last_name=user.last_name).exclude(id=user.id)
            for u in candidates_users:
                account_info = AccountInfo.build_for_user(u)
                self.stdout.write(str(account_info))
            if confirm_action("deactivate %d %s" % (user.id, str(user))):
                self._deactivate_user(user)

    def _deactivate_user(self, user):
        if not self._apply_changes:
            self.stdout.write('#', ending='')
        self.stdout.write("Deactivating user (id %d email %s username %s)\n" % (user.id, user.email, user.username))
        if self._apply_changes:
            user.email = 'deleted_' + str(uuid.uuid4())[:8] + '.' + user.email
            user.is_active = False
            user.save()

    def _process_empty_email_user(self, user):
        account_info = AccountInfo.build_for_user(user)

        if account_info.status == AccountInfo.Status.EMPTY:
            if user.is_staff:
                self._bad_staff_users.append(user)
                self.stdout.write('Found empty staff account without email: %s\n' % str(account_info))
            else:
                self._to_deactivate_users.append(user)
        else:
            self._bad_users.append(user)
            self.stdout.write('Found non-empty account without email: %s\n' % str(account_info))

    def _process_duplicated_emails(self, users):
        arr = []
        for user in users:
            if user.is_staff:
                raise Exception('email-duplicated account is staff')
            arr.append(AccountInfo.build_for_user(user))

        arr = sorted(arr)[::-1]
        self.stdout.write('Found %d users with same email %s (first %s) (second %s)\n'
                          % (len(arr), users[0].email, str(arr[0]), str(arr[1])))
        self._to_deactivate_users += map(operator.attrgetter('user'), arr[1:])
