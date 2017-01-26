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
        for person_history in data['ghist']:
            for history_entry in person_history:
                history_entry[1] = parse_roles(history_entry[1])

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
        created = update.get_changes(models.Role, Action.CREATE)
        deleted = update.get_changes(models.Role, Action.DELETE)
        self.describe_list(created, 'New roles', '+ ')
        self.describe_list(deleted, 'Deleted roles', '- ')

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
        role_by_id = cls._add_poldnev_roles_to_update(
            update, session_by_id, data['ghist'])
        cls._add_poldnev_history_entries_to_update(
            update, person_by_id, role_by_id, data['ghist'])
        return update

    @classmethod
    def _add_poldnev_sessions_to_update(cls, update, session_names,
                                        session_links):
        session_by_id = {s.poldnev_id : s for s in models.Session.objects.all()}
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

            if str(person_id) not in person_by_id:
                # Person is new
                person = models.Person(poldnev_id=person_id,
                                       first_name=first_names[person_id],
                                       middle_name=middle_names[person_id],
                                       last_name=last_names[person_id])
                person_by_id[str(person_id)] = person
                update.objects_to_save.append(person)
                update.add_change(person.__class__, Action.CREATE, str(person))
                continue

            person = person_by_id[str(person_id)]
            old_names = (person.first_name,
                         person.middle_name,
                         person.last_name)
            if old_names == new_names:
                # Person isn't changed
                person_ids_to_delete.remove(str(person_id))
                continue

            # Person is updated
            person_ids_to_delete.remove(str(person_id))

            old_str = str(person)
            person.first_name = first_names[person_id]
            person.middle_name = middle_names[person_id]
            person.last_name = last_names[person_id]
            update.objects_to_save.append(person)
            update.add_change(person.__class__,
                              Action.UPDATE,
                              '{} -> {}'.format(old_str, str(person)))

        for person_id in person_ids_to_delete:
            person = person_by_id[str(person_id)]
            update.objects_to_delete.append(person)
            update.add_change(person.__class__, Action.DELETE, str(person))

        return person_by_id

    @classmethod
    def _add_poldnev_roles_to_update(cls, update, session_by_id, history):
        role_by_id = {r.role_id : r for r in models.Role.objects.all()}
        role_ids_to_delete = {r_id for r_id in role_by_id}

        for history_entries in history:
            for session_id, roles in history_entries:
                session = session_by_id[session_id]
                for role_str in roles:
                    role = models.Role(session=session, poldnev_role=role_str)

                    if role.role_id in role_by_id:
                        # Role already exists. Nothing to update
                        role_ids_to_delete.discard(role.role_id)
                        continue

                    # Role is new
                    role_by_id[role.role_id] = role
                    update.objects_to_save.append(role)
                    update.add_change(role.__class__, Action.CREATE, str(role))

        for role_id in role_ids_to_delete:
            role = role_by_id[role_id]
            update.objects_to_delete.append(role)
            update.add_change(role.__class__, Action.DELETE, str(role))

        return role_by_id

    @classmethod
    def _add_poldnev_history_entries_to_update(cls, update, person_by_id,
                                               role_by_id, history):
        entry_by_id = {e.entry_id : e for e in models.HistoryEntry.objects.all()}
        entry_ids_to_delete = {r_id for r_id in entry_by_id}

        for person_id in range(1, len(history)):
            if not history[person_id]:
                continue

            person = person_by_id[str(person_id)]
            for session_id, roles in history[person_id]:
                for role_str in roles:
                # TODO(Artem Tabolin): don't compute id here
                    role_id = models.Role.make_id(session_id, role_str)
                    role = role_by_id[role_id]
                    entry = models.HistoryEntry(person=person, role=role)

                    if entry.entry_id in entry_by_id:
                        # History entry already exists. Nothing to update
                        entry_ids_to_delete.discard(entry.entry_id)
                        continue

                    # History entry is new
                    entry_by_id[entry.entry_id] = entry
                    update.objects_to_save.append(entry)
                    update.add_change(
                        entry.__class__, Action.CREATE, str(entry))

        for entry_id in entry_ids_to_delete:
            entry = entry_by_id[entry_id]
            update.objects_to_delete.append(entry)
            update.add_change(entry.__class__, Action.DELETE, str(entry))

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
                if isinstance(obj, models.Role):
                    obj.session_id = obj.session.id
                if isinstance(obj, models.HistoryEntry):
                    obj.role_id = obj.role.id
                    obj.person_id = obj.person.id
                obj.save()



def parse_roles(roles_str):
    """Parse the roles string from poldnev.ru and return the list of roles.

    For example, for the string:

    'финансовый директор, <a href=\"/lksh/2012.August/D\">D1.преп</a>'

    the method returns ['финансовый директор', 'D1.преп'].
    """
    roles_without_html = re.sub(r'<[^>]*>', '', roles_str)
    return roles_without_html.split(', ')
