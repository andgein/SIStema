import operator

from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

import frontend.table
import frontend.icons
import questionnaire.models
import questionnaire.views
from schools.decorators import school_view
import schools.models
import users.models
import sistema.staff
from sistema.helpers import group_by
import modules.study_results.models as study_results_models

class StudyResultsTable(frontend.table.Table):
    icon = frontend.icons.FaIcon('envelope-o')

    title = 'Результаты обучения в школе'

    def __init__(self, school, study_result_ids):
        super().__init__(
            study_results_models.StudyResult,
            study_results_models.StudyResult.objects.filter(
                id__in=study_result_ids).prefetch_related('comments')
        )
        self.school = school
        self.identifiers = {'school_name': school.short_name}

        self.about_questionnaire = (
            questionnaire.models.Questionnaire.objects
            .filter(short_name='about').first())
        self.enrollee_questionnaire = (
            questionnaire.models.Questionnaire
            .objects.filter(
                school=self.school,
                short_name='enrollee'
            ).first())
        # TODO: add search by name
        name_column = frontend.table.SimpleFuncColumn(
            lambda study_result: study_result.school_participant.user
                .get_full_name(), 'Имя')
        name_column.data_type = frontend.table.LinkDataType(
            frontend.table.StringDataType(),
            lambda study_result:
                reverse('study_results:study_result_user',
                    kwargs={'school_name': self.school.short_name, 
                            'user_id': study_result.school_participant.user.id})
        )

        parallel_column = frontend.table.SimpleFuncColumn(
            lambda study_result: study_result.school_participant.parallel.name, 
            'Параллель')
        theory_column = frontend.table.SimplePropertyColumn(
            'theory', 'Оценка теории', name='theory')
        practice_column = frontend.table.SimplePropertyColumn(
            'practice', 'Оценка практики', name='practice')
        comments_column = frontend.table.SimpleFuncColumn(
            self.comments, 'Комменты')
        comments_column.data_type = frontend.table.RawHtmlDataType()

        self.columns = (
            name_column,
            frontend.table.SimpleFuncColumn(self.city, 'Город'),
            frontend.table.SimpleFuncColumn(self.school_and_class,
                                            'Школа и класс'),
            parallel_column,
            theory_column,
            practice_column,
            comments_column,
        )

    # TODO: bad architecture :( create only for empty after_filter_applying
    @classmethod
    def create(cls, school):
        study_result_ids = get_study_result_ids(school)
        table = cls(school, study_result_ids)
        table.after_filter_applying()
        return table

    def after_filter_applying(self):
        filtered_users = list(self.paged_queryset.values_list(
            'school_participant__user_id', flat=True))
        self.about_questionnaire_answers = group_by(
            questionnaire.models.QuestionnaireAnswer.objects.filter(
                questionnaire=self.about_questionnaire,
                user__in=filtered_users
            ),
            operator.attrgetter('user_id')
        )
        self.enrollee_questionnaire_answers = group_by(
            questionnaire.models.QuestionnaireAnswer.objects.filter(
                questionnaire=self.enrollee_questionnaire,
                user__in=filtered_users
            ),
            operator.attrgetter('user_id')
        )


    def get_header(self):
        pass

    @classmethod
    def restore(cls, identifiers):
        school_name = identifiers['school_name'][0]
        school_qs = schools.models.School.objects.filter(short_name=school_name)
        if not school_qs.exists():
            raise NameError('Bad school name')
        _school = school_qs.first()
        study_result_ids = get_study_result_ids(_school)
        return cls(_school, study_result_ids)

    @staticmethod
    def _get_questionnaire_answer(questionnaire_answers, field):
        for answer in questionnaire_answers:
            if answer.question_short_name == field:
                return answer.answer
        return ''

    # TODO: future module profile
    def _get_user_about_field(self, study_result, field):
        return self._get_questionnaire_answer(
            self.about_questionnaire_answers[
                study_result.school_participant.user.id], field)

    def _get_user_enrollee_field(self, study_result, field):
        return self._get_questionnaire_answer(
            self.enrollee_questionnaire_answers[
                study_result.school_participant.user.id], field)

    def city(self, study_result):
        return self._get_user_about_field(study_result, 'city')

    def school_and_class(self, study_result):
        user_school = self._get_user_about_field(study_result, 'school')
        user_class = self._get_user_enrollee_field(study_result, 'class')
        if user_school == '':
            return '%s класс' % user_class
        return '%s, %s класс' % (user_school, user_class)

    @property
    def theory(self, study_result):
        return study_result.theory

    @property
    def practice(self, study_result):
        return study_result.practice

    def comments(self, study_result):
        return '\n'.join('<p>' + str(comment) + '</p>'
            for comment in study_result.comments.all())


def get_study_result_ids(school):
    study_result_ids = (schools.models.SchoolParticipant.objects.filter(
        school=school).select_related('study_result').all()
        .values_list('id', flat=True))
    return study_result_ids

@school_view
@sistema.staff.only_staff
def study_results(request):
    study_results_table = StudyResultsTable.create(request.school)
    return render(request, 'study_results/staff/study_results.html',
                  {'study_results_table': study_results_table})


@sistema.staff.only_staff
def study_results_school(request, school_name):
    school = get_object_or_404(schools.models.School, short_name=school_name)
    study_results_table = StudyResultsTable.create(school)
    return render(request, 'study_results/staff/study_results.html',
                  {'study_results_table': study_results_table})

#@sistema.staff.only_staff
def study_result_user(request, school_name, user_id): 
    school = get_object_or_404(schools.models.School, short_name=school_name)
    user = get_object_or_404(users.models.User, id=user_id)
    return render(request, 'study_results/staff/study_result_user.html',
                  {'user_name': user.get_full_name()})
