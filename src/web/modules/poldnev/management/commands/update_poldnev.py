# -*- coding: utf-8 -*-

import collections
import enum
import json
import re

from django.core.management import base as management_base
from django.db import transaction
import requests

from modules.poldnev import models


Action = enum.Enum('Action', ['NOTHING', 'DELETE', 'CREATE', 'UPDATE'])


class Command(management_base.BaseCommand):
    help = 'Update content of poldnev module from poldnev.ru'

    DATA_URL = 'http://poldnev.ru/lksh/js/api_main.js'

    def handle(self, *args, **options):
        self.stdout.write('Fetching {}...'.format(self.DATA_URL))

        response = requests.get(self.DATA_URL)
        if not response.ok:
            raise management_base.CommandError(
                'Cannot fetch {}. Status: {} {}.'.format(self.DATA_URL,
                                                         response.status_code,
                                                         response)
            )

        self.stdout.write('Parsing JSON...')

        data = json.loads(response.text)

        self.stdout.write('Processing data...')
        update = PoldnevUpdate.from_poldnev_data(data)

        if update.is_empty:
            self.stdout.write('poldnev module is up to date.')
            return

        self.describe_update(update)

        self.stdout.write('')
        while True:
            answer = input('Save changes to the database (y/n): ')
            if answer == 'y':
                update.apply()
                self.stdout.write(self.style.SUCCESS(
                    'poldnev module is successfully updated.'))
                break
            elif answer == 'n':
                self.stdout.write('No changes were applied.')
                break

    def describe_update(self, update):
        self.stdout.write('')
        created = update.get_changes(models.Session, Action.CREATE)
        updated = update.get_changes(models.Session, Action.UPDATE)
        deleted = update.get_changes(models.Session, Action.DELETE)
        self.describe_list(created, 'New sessions', '+ ')
        self.describe_list(updated, 'Updated sessions', '~ ')
        self.describe_list(deleted, 'Deleted sessions', '- ')

        self.stdout.write('')
        created = update.get_changes(models.Person, Action.CREATE)
        updated = update.get_changes(models.Person, Action.UPDATE)
        deleted = update.get_changes(models.Person, Action.DELETE)
        self.describe_list(created, 'New persons', '+ ')
        self.describe_list(updated, 'Updated persons', '~ ')
        self.describe_list(deleted, 'Deleted persons', '- ')

        self.stdout.write('')
        created = update.get_changes(models.Parallel, Action.CREATE)
        deleted = update.get_changes(models.Parallel, Action.DELETE)
        self.describe_list(created, 'New parallels', '+ ')
        self.describe_list(deleted, 'Deleted parallels', '- ')

        self.stdout.write('')
        created = update.get_changes(models.StudyGroup, Action.CREATE)
        deleted = update.get_changes(models.StudyGroup, Action.DELETE)
        self.describe_list(created, 'New study groups', '+ ')
        self.describe_list(deleted, 'Deleted study groups', '- ')

        self.stdout.write('')
        created = update.get_changes(models.HistoryEntry, Action.CREATE)
        deleted = update.get_changes(models.HistoryEntry, Action.DELETE)
        self.describe_list(created, 'New history entries', '+ ')
        self.describe_list(deleted, 'Deleted history entries', '- ')

    def describe_list(self, lst, title, prefix, limit=10):
        self.stdout.write('{}: {}'.format(title, len(lst)))
        for line in lst[:limit]:
            self.stdout.write(prefix + line)
        if len(lst) > limit:
            self.stdout.write('...')


class PoldnevUpdate:
    POLDNEV_ROOT = 'https://poldnev.ru'

    @classmethod
    def from_poldnev_data(cls, data):
        update = cls()
        session_by_id = cls._add_poldnev_sessions_to_update(
            update, data['glname'], data['gsmlink'])
        person_by_id = cls._add_poldnev_persons_to_update(
            update, data['gname'], data['gpatr'], data['gsur'])
        cls._add_poldnev_history_entries_to_update(
            update, session_by_id, person_by_id, data['ghist'])
        return update

    @classmethod
    def _add_poldnev_sessions_to_update(cls, update, session_names,
                                        session_links):
        session_by_id = {s.poldnev_id: s for s in models.Session.objects.all()}
        session_ids_to_delete = {s_id for s_id in session_by_id}

        for session_id, session_name in session_names.items():
            if session_id in session_links:
                session_url = cls.POLDNEV_ROOT + session_links[session_id]
            else:
                session_url = None

            if session_id not in session_by_id:
                # Session is new
                session = models.Session(poldnev_id=session_id,
                                         name=session_name,
                                         url=session_url)
                session_by_id[session_id] = session
                update.objects_to_save.append(session)
                update.add_change(session.__class__, Action.CREATE, str(session))
                continue

            session = session_by_id[session_id]
            session_ids_to_delete.remove(session_id)
            if session_name == session.name and session_url == session.url:
                # Session isn't changed
                continue

            # Session is updated
            old_str = '{} ({})'.format(session, session.url)
            session.name = session_name
            session.url = session_url
            new_str = '{} ({})'.format(session, session.url)
            update.objects_to_save.append(session)
            update.add_change(session.__class__,
                              Action.UPDATE,
                              '{} -> {}'.format(old_str, new_str))

        for session_id in session_ids_to_delete:
            session = session_by_id[session_id]
            update.objects_to_delete.append(session)
            update.add_change(session.__class__, Action.DELETE, str(session))

        return session_by_id

    @classmethod
    def _add_poldnev_persons_to_update(cls, update, first_names, middle_names,
                                       last_names):
        person_by_id = {p.poldnev_id : p for p in models.Person.objects.all()}
        person_ids_to_delete = {p_id for p_id in person_by_id}

        for person_id in range(1, len(first_names)):
            new_names = (first_names[person_id],
                         middle_names[person_id],
                         last_names[person_id])

            # Skip gaps
            if new_names == ('', '', ''):
                continue

            if person_id not in person_by_id:
                # Person is new
                person = models.Person(poldnev_id=person_id,
                                       first_name=first_names[person_id],
                                       middle_name=middle_names[person_id],
                                       last_name=last_names[person_id])
                person_by_id[person_id] = person
                update.objects_to_save.append(person)
                update.add_change(person.__class__, Action.CREATE, str(person))
                continue

            person = person_by_id[person_id]
            old_names = (person.first_name,
                         person.middle_name,
                         person.last_name)
            if old_names == new_names:
                # Person isn't changed
                person_ids_to_delete.remove(person_id)
                continue

            # Person is updated
            person_ids_to_delete.remove(person_id)

            old_str = str(person)
            person.first_name = first_names[person_id]
            person.middle_name = middle_names[person_id]
            person.last_name = last_names[person_id]
            update.objects_to_save.append(person)
            update.add_change(person.__class__,
                              Action.UPDATE,
                              '{} -> {}'.format(old_str, str(person)))

        for person_id in person_ids_to_delete:
            person = person_by_id[person_id]
            update.objects_to_delete.append(person)
            update.add_change(person.__class__, Action.DELETE, str(person))

        return person_by_id

    @classmethod
    def _add_poldnev_history_entries_to_update(cls, update, session_by_id,
                                               person_by_id, history):
        parallel_by_id = {p.unique_key: p for p in models.Parallel.objects.all()}
        parallel_ids_to_delete = {p_id for p_id in parallel_by_id}

        study_group_by_id = {g.unique_key: g for g in models.StudyGroup.objects.all()}
        study_group_ids_to_delete = {g_id for g_id in study_group_by_id}

        entry_by_id = {e.unique_key: e for e in models.HistoryEntry.objects.all()}
        entry_ids_to_delete = {e_id for e_id in entry_by_id}

        for person_id in range(1, len(history)):
            if not history[person_id]:
                continue

            person = person_by_id[person_id]
            for session_id, roles in history[person_id]:
                session = session_by_id[session_id]
                for role_str in roles.split(', '):
                    parallel_name, study_group_name, role = parse_role(role_str)
                    parallel = None
                    if parallel_name:
                        # sys.stderr.write('parallel %s\n' % parallel_name)
                        parallel = models.Parallel(session=session, name=parallel_name)
                        parallel = cls.create_or_update_by_unique_key(update, parallel_by_id,
                                                                      parallel_ids_to_delete, parallel)

                    study_group = None
                    if study_group_name:
                        # sys.stderr.write('study_group %s\n' % study_group_name)
                        study_group = models.StudyGroup(parallel=parallel, name=study_group_name)
                        study_group = cls.create_or_update_by_unique_key(update, study_group_by_id,
                                                                         study_group_ids_to_delete, study_group)

                    # sys.stderr.write('role %s\n' % role)
                    entry = models.HistoryEntry(person=person, session=session, study_group=study_group, role=role)
                    cls.create_or_update_by_unique_key(update, entry_by_id, entry_ids_to_delete, entry)

        cls.delete_all(update, parallel_by_id, parallel_ids_to_delete)
        cls.delete_all(update, study_group_by_id, study_group_ids_to_delete)
        cls.delete_all(update, entry_by_id, entry_ids_to_delete)

    @classmethod
    def delete_all(cls, update, obj_by_id, obj_ids_to_delete):
        for obj_id in obj_ids_to_delete:
            obj = obj_by_id[obj_id]
            update.objects_to_delete.append(obj)
            update.add_change(obj.__class__, Action.DELETE, str(obj))

    @classmethod
    def create_or_update_by_unique_key(cls, update, obj_by_key, obj_keys_to_delete, obj):
        key = obj.unique_key
        if key in obj_by_key:
            # Object already exists. Nothing to update
            obj_keys_to_delete.discard(key)
            return obj_by_key[key]

        # Object is new
        obj_by_key[key] = obj
        update.objects_to_save.append(obj)
        update.add_change(obj.__class__, Action.CREATE, str(obj))
        return obj

    def __init__(self):
        self._diff = collections.defaultdict(list)
        self.objects_to_save = []
        self.objects_to_delete = []

    def add_change(self, cls, action, string):
        self._diff[(cls.__name__, action)].append(string)

    def get_changes(self, cls, action):
        return self._diff[(cls.__name__, action)]

    @property
    def is_empty(self):
        return len(self.objects_to_delete) == len(self.objects_to_save) == 0

    def apply(self):
        with transaction.atomic():
            for obj in self.objects_to_delete:
                obj.delete()

            for obj in self.objects_to_save:
                if isinstance(obj, models.Parallel):
                    obj.session_id = obj.session.pk
                if isinstance(obj, models.StudyGroup):
                    obj.parallel_id = obj.parallel.pk
                if isinstance(obj, models.HistoryEntry):
                    obj.person_id = obj.person.pk
                    obj.session_id = obj.session.pk
                    if obj.study_group:
                        obj.study_group_id = obj.study_group.pk
                obj.save()


def parse_role(role_str):
    """Parse the role string from poldnev.ru and return the tuple of
    (parallel_name, study_group_name, role).

    For example, for the string:

    'финансовый директор' returns (None, None, 'финансовый директор'),
    '<a href="/lksh/2012.August/D">D1.преп</a>' returns ('D', 'D1', 'преп'),
    '<a href="/lksh/2014.July/C.py">C1.py</a>' returns ('C.py', 'C1.py', ''),
    '<a href="/lksh/2014.Winter/C.py+">C.py+.преп</a>' returns ('C.py+', 'C.py+', 'преп'),
    '<a href="/lksh/2006/A">A1.преп-стажер</a>' returns ('A', 'A1', 'преп-стажер'),
    '<a href="">?</a>' returns (None, None, '?')

    """
    if not role_str.startswith('<'):
        return None, None, role_str
    if role_str == '<a href="">?</a>':
        return None, None, '?'

    m = re.match(r'^<a.*/([^/]+)">(.+)\.(преп.*)</a>$', role_str)
    if m:
        return m.group(1), m.group(2), m.group(3)
    m = re.match(r'^<a.*/([^/]+)">(.+)</a>$', role_str)
    return m.group(1), m.group(2), ''
