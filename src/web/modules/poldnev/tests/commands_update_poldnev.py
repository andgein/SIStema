# -*- coding: utf-8 -*-

"""Tests for poldnev.management.commands.update_poldnev"""

import operator

import django.test

# TODO(Artem Tabolin): find a way not to depend on location of poldnev module
from modules.poldnev import models
from modules.poldnev.management.commands import update_poldnev


class UpdatePoldnevTestCase(django.test.TestCase):
    def test_update_sessions(self):
        """Sessions are correctly updated"""

        # Initialize db
        self._initialize_sessions()

        # New data
        new_session_names = {
            '2048.mars': 'ЛКШ.2048.Марс',  # update
            '2048.july': 'ЛКШ.2048.Июль',  # create
            '2048.august': 'ЛКШ.2048.Август',  # unchanged
        }

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_sessions_to_update(update, new_session_names, {})

        self.assertEqual(
            update.get_changes(models.Session, update_poldnev.Action.CREATE),
            ['ЛКШ.2048.Июль'])
        self.assertEqual(
            update.get_changes(models.Session, update_poldnev.Action.UPDATE),
            ['ЛКШ.2048.Мурс (None) -> ЛКШ.2048.Марс (None)'])
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
            ' '.join([last_names[i], first_names[i], middle_names[i]])
            for i in range(len(first_names))
            if first_names[i] + middle_names[i] + last_names[i]]

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_persons_to_update(
            update, first_names, middle_names, last_names)

        self.assertEqual(
            update.get_changes(models.Person, update_poldnev.Action.CREATE),
            ['Броварь Ирина Владимировна (4)'])
        self.assertEqual(
            update.get_changes(models.Person, update_poldnev.Action.UPDATE),
            ['Лопатин Андрей Сергеевич (2) -> Станкевич Андрей Сергеевич (2)'])
        self.assertEqual(
            update.get_changes(models.Person, update_poldnev.Action.DELETE),
            ['Пушкин Александр Сергеевич (1)'])

        update.apply()

        self.assertQuerysetEqual(models.Person.objects.all(),
                                 new_persons_full_names,
                                 transform=operator.attrgetter('full_name'),
                                 ordered=False)

    def test_parse_role(self):
        self.assertEqual((None, None, 'финансовый директор'), update_poldnev.parse_role('финансовый директор'))
        self.assertEqual(('D', 'D1', 'преп'), update_poldnev.parse_role('<a href="/lksh/2012.August/D">D1.преп</a>'))
        self.assertEqual(('C.py', 'C1.py', ''), update_poldnev.parse_role('<a href="/lksh/2014.July/C.py">C1.py</a>'))
        self.assertEqual(('C.py+', 'C.py+', 'преп'), update_poldnev.parse_role('<a href="/lksh/2014.Winter/C.py+">C.py+.преп</a>'))
        self.assertEqual(('A', 'A1', 'преп-стажер'), update_poldnev.parse_role('<a href="/lksh/2006/A">A1.преп-стажер</a>'))
        self.assertEqual((None, None, '?'), update_poldnev.parse_role('<a href="">?</a>'))

    def test_update_history_entries(self):
        """Parallels, study groups and history entries are correctly updated"""

        # Initialize db
        self._initialize_history_entries()

        # New data
        history = [
            [],
            [
                ['2048.august', 'поэт, <a href="/lksh/2048.August/B">B2.преп</a>'],
            ],
            [
                ['2048.august', 'пилот квадрокоптера, поэт, <a href="/lksh/2048.August/B">B1</a>'],
            ],
            [
                ['2048.august', '<a href="/lksh/2048.August/D">D1.преп</a>'],
            ],
            [],
        ]

        person_by_id = {p.poldnev_id: p for p in models.Person.objects.all()}
        session_by_id = {s.poldnev_id: s for s in models.Session.objects.all()}

        update = update_poldnev.PoldnevUpdate()
        update._add_poldnev_history_entries_to_update(
            update, session_by_id, person_by_id, history)

        self.assertEqual(
            update.get_changes(models.Parallel,
                               update_poldnev.Action.CREATE),
            ['ЛКШ.2048.Август D'])
        self.assertEqual(
            update.get_changes(models.Parallel,
                               update_poldnev.Action.UPDATE),
            [])
        self.assertEqual(
            update.get_changes(models.Parallel,
                               update_poldnev.Action.DELETE),
            ['ЛКШ.2048.Август A'])

        self.assertEqual(
            update.get_changes(models.StudyGroup,
                               update_poldnev.Action.CREATE),
            ['ЛКШ.2048.Август B B2', 'ЛКШ.2048.Август D D1'])
        self.assertEqual(
            update.get_changes(models.StudyGroup,
                               update_poldnev.Action.UPDATE),
            [])
        self.assertEqual(
            update.get_changes(models.StudyGroup,
                               update_poldnev.Action.DELETE),
            ['ЛКШ.2048.Август A A0'])

        self.assertEqual(
            update.get_changes(models.HistoryEntry,
                               update_poldnev.Action.CREATE),
            ['Пушкин Александр Сергеевич (ЛКШ.2048.Август: B2.преп)',
             'Лопатин Андрей Сергеевич (ЛКШ.2048.Август: пилот квадрокоптера)',
             'Лопатин Андрей Сергеевич (ЛКШ.2048.Август: поэт)',
             'Мельников Сергей Вячеславович (ЛКШ.2048.Август: D1.преп)',
             ])
        self.assertEqual(
            update.get_changes(models.HistoryEntry,
                               update_poldnev.Action.UPDATE),
            [])
        self.assertEqual(
            update.get_changes(models.HistoryEntry,
                               update_poldnev.Action.DELETE),
            ['Мельников Сергей Вячеславович (ЛКШ.2048.Август: король бездельников)'])

        update.apply()

        new_parallels = [
            'ЛКШ.2048.Август B',
            'ЛКШ.2048.Август D',
        ]
        new_study_groups = [
            'ЛКШ.2048.Август B B1',
            'ЛКШ.2048.Август B B2',
            'ЛКШ.2048.Август D D1',
        ]
        new_entries = [
            'Лопатин Андрей Сергеевич (ЛКШ.2048.Август: пилот квадрокоптера)',
            'Лопатин Андрей Сергеевич (ЛКШ.2048.Август: поэт)',
            'Лопатин Андрей Сергеевич (ЛКШ.2048.Август: B1)',
            'Пушкин Александр Сергеевич (ЛКШ.2048.Август: поэт)',
            'Пушкин Александр Сергеевич (ЛКШ.2048.Август: B2.преп)',
            'Мельников Сергей Вячеславович (ЛКШ.2048.Август: D1.преп)',
        ]
        self.assertQuerysetEqual(
            models.Parallel.objects.all(),
            new_parallels,
            transform=str,
            ordered=False)
        self.assertQuerysetEqual(
            models.StudyGroup.objects.all(),
            new_study_groups,
            transform=str,
            ordered=False)
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

    def _initialize_history_entries(self):
        self._initialize_persons()
        self._initialize_sessions()
        session = models.Session.objects.get(poldnev_id='2048.august')
        parallelA = models.Parallel.objects.create(session=session, name='A')
        models.StudyGroup.objects.create(parallel=parallelA, name='A0')
        parallelB = models.Parallel.objects.create(session=session, name='B')
        groupB1 = models.StudyGroup.objects.create(parallel=parallelB, name='B1')

        pushkin = models.Person.objects.get(poldnev_id=1)
        lopatin = models.Person.objects.get(poldnev_id=2)
        melnikov = models.Person.objects.get(poldnev_id=3)

        models.HistoryEntry.objects.create(person=pushkin, session=session, role='поэт')
        models.HistoryEntry.objects.create(person=lopatin, session=session, study_group=groupB1, role='')
        models.HistoryEntry.objects.create(person=melnikov, session=session, role='король бездельников')
