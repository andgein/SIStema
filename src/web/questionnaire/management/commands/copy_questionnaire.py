# -*- coding: utf-8 -*-

from django.core.management import base as management_base

from questionnaire import models
import schools.models


class Command(management_base.BaseCommand):
    help = """Make a copy of the questionnaire"""

    def handle(self, *args, **options):
        from_school = self.choose_school(
            intro_text='Choose a school to copy questionnaire from:',
        )
        from_questionnaire = self.choose_questionnaire(
            intro_text='Choose a questionnaire to copy:',
            school=from_school,
        )
        if from_questionnaire is None:
            if from_school is None:
                print('There is no global questionnaires')
            else:
                print('There is no questionnaires for', from_school)
            return
        to_school = self.choose_school(
            intro_text='Choose a school to copy questionnaire to:',
        )
        self.copy_questionnaire(from_questionnaire, to_school)

    def copy_questionnaire(self, src_questionnaire, to_school):
        print('Copying {} to {}'.format(src_questionnaire, to_school))
        dst_short_name = input(
            'Enter new questionnaire short name or leave blank to keep '
            'unchanged [{}]:'.format(src_questionnaire.short_name)
        ) or src_questionnaire.short_name
        dst_session = None
        if src_questionnaire.session is not None:
            dst_session_choices = [None]
            dst_session_choices.extend(to_school.sessions.all())
            if len(dst_session_choices) > 1:
                for i, session in enumerate(dst_session_choices):
                    print('{}) {}'.format(i + 1, session))
                dst_session = self.choose_from_choices(dst_session_choices)

        # TODO: choose from school's and global key dates
        return src_questionnaire.clone(
            new_school=to_school,
            new_short_name=dst_short_name,
            new_session=dst_session,
        )

    def choose_school(self, intro_text='Choose a school:'):
        school_choices = schools.models.School.objects.order_by('-year', '-name')
        print(intro_text)
        for i, school in enumerate(school_choices):
            print('{}) {}'.format(i + 1, school.name))
        return self.choose_from_choices(
            choices=school_choices,
            question_text='Enter the school number: ',
        )

    def choose_questionnaire(self,
                             school=None,
                             intro_text='Choose a questionnaire:'):
        questionnaire_choices = (
            models.Questionnaire.objects.filter(school=school))
        if not questionnaire_choices.exists():
            return None
        print(intro_text)
        for i, questionnaire in enumerate(questionnaire_choices):
            print('{}) {} - {}'.format(
                i + 1, questionnaire.short_name, questionnaire.title))
        return self.choose_from_choices(
            choices=questionnaire_choices,
            question_text='Enter the questionnaire number: ',
        )

    def choose_session_for_school(self, school, intro_text='Choose session:'):
        session_choices = school.sessions.all()
        if not session_choices.exists():
            return None
        print(intro_text)
        for i, session in enumerate(session_choices):
            print('{}) {}', i + 1, session)
        return self.choose_from_choices(
            choices=session_choices,
            question_text='Choose a session: ',
        )

    @staticmethod
    def choose_from_choices(choices, question_text='Enter the option number: '):
        while True:
            choice_i_str = input(question_text)
            try:
                choice_i = int(choice_i_str) - 1
            except ValueError:
                continue
            if 0 <= choice_i < len(choices):
                return choices[choice_i]
