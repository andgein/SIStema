# -*- coding: utf-8 -*-

"""Tests for poldnev.management.commands.update_poldnev"""

import unittest

import django.test

# TODO(Artem Tabolin): find a way not to depend on location of poldnev module
from modules.poldnev import models
from modules.poldnev.management.commands import update_poldnev


class UpdatePoldnevTestCase(django.test.TestCase):
    def setUp(self):
        pass

    def test_update_sessions(self):
        """Sessions are correctly updated"""

        # Initialize db
        self._initialize_sessions()

        # New data
        new_session_names = {
            '2048.mars' : 'ЛКШ.2048.Марс', # update
            '2048.july' : 'ЛКШ.2048.Июль', # create
            '2048.august' : 'ЛКШ.2048.Август', # unchanged
        }

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_sessions_to_update(update, new_session_names)

        self.assertEqual(
            update.get_changes(models.Session, update_poldnev.Action.CREATE),
            ['ЛКШ.2048.Июль'])
        self.assertEqual(
            update.get_changes(models.Session, update_poldnev.Action.UPDATE),
            ['ЛКШ.2048.Мурс -> ЛКШ.2048.Марс'])
        self.assertEqual(
            update.get_changes(models.Session, update_poldnev.Action.DELETE),
            ['ЛКШ.2048.Венера'])


        update.apply()
        
        self.assertQuerysetEqual(models.Session.objects.all(),
                                 new_session_names.values(),
                                 transform=str,
                                 ordered=False)

    def test_update_persons(self):
        """Persons are correctly updated"""

        # Initialize db
        self._initialize_persons()

        # New data
        first_names = ['', '', 'Андрей', 'Сергей', 'Ирина']
        middle_names = ['', '', 'Сергеевич', 'Вячеславович', 'Владимировна']
        last_names = ['', '', 'Станкевич', 'Мельников', 'Броварь']

        new_persons_full_names = [
            ' '.join([first_names[i], middle_names[i], last_names[i]])
            for i in range(len(first_names))
            if first_names[i] + middle_names[i] + last_names[i]]

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_persons_to_update(
            update, first_names, middle_names, last_names)

        self.assertEqual(
            update.get_changes(models.Person, update_poldnev.Action.CREATE),
            ['Ирина Владимировна Броварь'])
        self.assertEqual(
            update.get_changes(models.Person, update_poldnev.Action.UPDATE),
            ['Андрей Сергеевич Лопатин -> Андрей Сергеевич Станкевич'])
        self.assertEqual(
            update.get_changes(models.Person, update_poldnev.Action.DELETE),
            ['Александр Сергеевич Пушкин'])


        update.apply()

        self.assertQuerysetEqual(models.Person.objects.all(),
                                 new_persons_full_names,
                                 transform=str,
                                 ordered=False)

    def test_update_roles(self):
        """Roles are correctly updated"""

        # Initialize db
        self._initialize_roles()

        # New data
        history = [
            [],
            [
                ['2048.august', ['преп']],
            ],
            [
                ['2048.august', ['пилот квадрокоптера']],
                ['2048.mars', ['преп']],
            ],
        ]

        session_by_id = {s.poldnev_id : s for s in models.Session.objects.all()}

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_roles_to_update(update, session_by_id, history)

        self.assertEqual(
            update.get_changes(models.Role, update_poldnev.Action.CREATE),
            ['ЛКШ.2048.Август: преп', 'ЛКШ.2048.Мурс: преп'])
        self.assertEqual(
            update.get_changes(models.Role, update_poldnev.Action.UPDATE),
            [])
        self.assertEqual(
            update.get_changes(models.Role, update_poldnev.Action.DELETE),
            ['ЛКШ.2048.Август: поэт'])


        update.apply()

        self.assertQuerysetEqual(
            models.Role.objects.all(),
            [
                'ЛКШ.2048.Август: преп',
                'ЛКШ.2048.Мурс: преп',
                'ЛКШ.2048.Август: пилот квадрокоптера',
            ],
            transform=str,
            ordered=False)

    def test_update_history_entries(self):
        """History entries are correctly updated"""

        # Initialize db
        self._initialize_history_entries()

        # New data
        history = [
            [],
            [
                ['2048.august', ['поэт']],
            ],
            [
                ['2048.august', ['поэт', 'пилот квадрокоптера']],
            ],
            [],
        ]

        person_by_id = {p.poldnev_id : p for p in models.Person.objects.all()}
        role_by_id = {r.role_id : r for r in models.Role.objects.all()}

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_history_entries_to_update(
            update, person_by_id, role_by_id, history)

        self.assertEqual(
            update.get_changes(models.HistoryEntry,
                               update_poldnev.Action.CREATE),
            ['Андрей Сергеевич Лопатин (ЛКШ.2048.Август: пилот квадрокоптера)'])
        self.assertEqual(
            update.get_changes(models.HistoryEntry,
                               update_poldnev.Action.UPDATE),
            [])
        self.assertEqual(
            update.get_changes(models.HistoryEntry,
                               update_poldnev.Action.DELETE),
            ['Сергей Вячеславович Мельников '
             '(ЛКШ.2048.Август: пилот квадрокоптера)'])


        update.apply()

        new_entries = [
            'Андрей Сергеевич Лопатин (ЛКШ.2048.Август: пилот квадрокоптера)',
            'Андрей Сергеевич Лопатин (ЛКШ.2048.Август: поэт)',
            'Александр Сергеевич Пушкин (ЛКШ.2048.Август: поэт)',
        ]

        self.assertQuerysetEqual(
            models.HistoryEntry.objects.all(),
            new_entries,
            transform=str,
            ordered=False)

    def _initialize_sessions(self):
        models.Session.objects.create(poldnev_id='2048.august',
                                      name='ЛКШ.2048.Август')
        models.Session.objects.create(poldnev_id='2048.mars',
                                      name='ЛКШ.2048.Мурс')
        models.Session.objects.create(poldnev_id='2048.venera',
                                      name='ЛКШ.2048.Венера')

    def _initialize_persons(self):
        models.Person.objects.create(poldnev_id='1',
                                     first_name='Александр',
                                     middle_name='Сергеевич',
                                     last_name='Пушкин')
        models.Person.objects.create(poldnev_id='2',
                                     first_name='Андрей',
                                     middle_name='Сергеевич',
                                     last_name='Лопатин')
        models.Person.objects.create(poldnev_id='3',
                                     first_name='Сергей',
                                     middle_name='Вячеславович',
                                     last_name='Мельников')

    def _initialize_roles(self):
        self._initialize_sessions()
        session = models.Session.objects.get(poldnev_id='2048.august')

        models.Role.objects.create(session=session,
                                   poldnev_role='пилот квадрокоптера')
        models.Role.objects.create(session=session,
                                   poldnev_role='поэт')

    def _initialize_history_entries(self):
        self._initialize_persons()
        self._initialize_roles()
        session = models.Session.objects.get(poldnev_id='2048.august')
        poet = models.Role.objects.get(session=session, poldnev_role='поэт')
        pilot = models.Role.objects.get(session=session,
                                        poldnev_role='пилот квадрокоптера')
        pushkin = models.Person.objects.get(poldnev_id=1)
        lopatin = models.Person.objects.get(poldnev_id=2)
        melnikov = models.Person.objects.get(poldnev_id=3)

        models.HistoryEntry.objects.create(person=pushkin, role=poet)
        models.HistoryEntry.objects.create(person=lopatin, role=poet)
        models.HistoryEntry.objects.create(person=melnikov, role=pilot)
