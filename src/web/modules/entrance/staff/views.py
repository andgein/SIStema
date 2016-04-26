import operator
import datetime

from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.http.response import Http404, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404

import frontend.table
import frontend.icons
import questionnaire.models
from modules.ejudge.models import SolutionCheckingResult
from school.decorators import school_view
import school.models
import sistema.staff
import modules.topics.models
import user.models
from . import forms
from .. import models
from ..views import get_base_entrance_level, get_entrance_tasks
from sistema.helpers import group_by, respond_as_attachment


class EnrollingUsersTable(frontend.table.Table):
    icon = frontend.icons.FaIcon('envelope-o')

    title = 'Подавшие заявку'

    def __init__(self, school, users_ids):
        super().__init__(user.models.User, user.models.User.objects.filter(id__in=users_ids))
        self.school = school
        self.identifiers = {'school_name': school.short_name}

        self.about_questionnaire = questionnaire.models.Questionnaire.objects.filter(short_name='about').first()
        self.enrollee_questionnaire = questionnaire.models.Questionnaire.objects.filter(
                for_school=self.school,
                short_name='enrollee'
        ).first()

        name_column = frontend.table.SimplePropertyColumn('get_full_name', 'Имя', search_attrs=['first_name', 'last_name'])
        name_column.data_type = frontend.table.LinkDataType(
                frontend.table.StringDataType(),
                lambda user: reverse('school:entrance:enrolling_user', args=(self.school.short_name, user.id))
        )

        email_column = frontend.table.SimplePropertyColumn('email', 'Почта')
        email_column.data_type = frontend.table.LinkDataType(
                frontend.table.StringDataType(),
                lambda user: 'mailto:%s' % user.email
        )

        self.columns = (name_column,
                        email_column,
                        frontend.table.SimpleFuncColumn(self.city, 'Город'),
                        frontend.table.SimpleFuncColumn(self.school_and_class, 'Школа и класс')
                        )

    # TODO: bad architecture :(
    # We need to define create for calling .after_filter_applying() without any filter.
    # Need refactoring
    @classmethod
    def create(cls, school):
        users_ids = get_enrolling_users_ids(school)
        table = cls(school, users_ids)
        table.after_filter_applying()
        return table

    def after_filter_applying(self):
        # TODO: use only id's via .values_list('id', flat=True)?
        filtered_users = list(self.paged_queryset)

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
        school_qs = school.models.School.objects.filter(short_name=school_name)
        if not school_qs.exists():
            raise NameError('Bad school name')
        _school = school_qs.first()
        users_ids = get_enrolling_users_ids(_school)
        return cls(_school, users_ids)

    @staticmethod
    def _get_questionnaire_answer(questionnaire_answers, field):
        for answer in questionnaire_answers:
            if answer.question_short_name == field:
                return answer.answer
        return ''

    def _get_user_about_field(self, user, field):
        return self._get_questionnaire_answer(self.about_questionnaire_answers[user.id], field)

    def _get_user_enrollee_field(self, user, field):
        return self._get_questionnaire_answer(self.enrollee_questionnaire_answers[user.id], field)

    def city(self, user):
        return self._get_user_about_field(user, 'city')

    def school_and_class(self, user):
        user_school = self._get_user_about_field(user, 'school')
        user_class = self._get_user_enrollee_field(user, 'class')
        if user_school == '':
            return '%s класс' % user_class
        return '%s, %s класс' % (user_school, user_class)


def get_enrolling_users_ids(school):
    # TODO: get not first TopicQuestionnaire, but defined in settings
    topic_questionnaire = modules.topics.models.TopicQuestionnaire.objects.filter(for_school=school).first()
    return topic_questionnaire.get_filled_users_ids()


@school_view
@sistema.staff.only_staff
def enrolling(request):
    users_table = EnrollingUsersTable.create(request.school)
    return render(request, 'entrance/staff/enrolling.html', {'users_table': users_table})


def _remove_old_checking_locks():
    models.CheckingLock.objects.filter(locked_until__lt=datetime.datetime.now()).delete()


@school_view
@sistema.staff.only_staff
def check(request):
    _remove_old_checking_locks()
    checking_groups = models.CheckingGroup.objects.filter(for_school=request.school) \
        .annotate(users_count=Count('userincheckinggroup'))
    return render(request, 'entrance/staff/check.html', {
        'checking_groups': checking_groups,
    })


@school_view
@sistema.staff.only_staff
def results(request):
    return None


def check_user(request, user_for_checking, checking_group=None):
    entrance_exam = models.EntranceExam.objects.filter(for_school=request.school).first()
    base_entrance_level = get_base_entrance_level(request.school, user_for_checking)
    level_upgrades = models.EntranceLevelUpgrade.objects.filter(upgraded_to__for_school=request.school,
                                                                user=user_for_checking)
    tasks = get_entrance_tasks(request.school, user_for_checking, base_entrance_level)
    tasks_solutions = group_by(
            models.EntranceExamTaskSolution.objects.filter(task__exam=entrance_exam, user=user_for_checking).order_by(
                    '-created_at'),
            operator.attrgetter('task_id')
    )
    for task in tasks:
        task.user_solutions = tasks_solutions[task.id]
        if hasattr(task, 'testentranceexamtask'):
            for solution in task.user_solutions:
                solution.is_correct = task.testentranceexamtask.check_solution(solution.solution)
            task.is_solved = any([s.is_correct for s in task.user_solutions])
            task.is_last_correct = len(task.user_solutions) > 0 and task.user_solutions[0].is_correct
        if hasattr(task, 'programentranceexamtask'):
            task.user_solutions = [s.programentranceexamtasksolution for s in task.user_solutions]
            task.is_solved = any(
                    [isinstance(s.result, SolutionCheckingResult) and s.result.is_success for s in task.user_solutions])
        if hasattr(task, 'fileentranceexamtask'):
            task.user_solutions = [s.fileentranceexamtasksolution for s in task.user_solutions]
            task.last_solution = task.user_solutions[0] if len(task.user_solutions) else None
            task.mark_field_id = 'tasks__file__mark_%d' % task.id

    test_tasks = list(filter(lambda t: hasattr(t, 'testentranceexamtask'), tasks))
    file_tasks = list(filter(lambda t: hasattr(t, 'fileentranceexamtask'), tasks))
    program_tasks = list(filter(lambda t: hasattr(t, 'programentranceexamtask'), tasks))

    file_tasks_mark_form = forms.FileEntranceExamTasksMarkForm(file_tasks, initial={'user_id': user_for_checking.id})
    comment_form = forms.EntranceCommentForm(initial={'user_id': user_for_checking.id})
    checking_groups = models.CheckingGroup.objects.filter(for_school=request.school)
    checking_groups = [(g.id, g.name) for g in checking_groups]
    put_into_checking_group_form = forms.PutIntoCheckingGroupForm(checking_groups, initial={'user_id': user_for_checking.id})

    return render(request, 'entrance/staff/check_user.html', {
        'checking_group': checking_group,
        'user_for_checking': user_for_checking,
        'base_entrance_level': base_entrance_level,
        'level_upgrades': level_upgrades,
        'test_tasks': test_tasks,
        'file_tasks': file_tasks,
        'program_tasks': program_tasks,
        'file_tasks_mark_form': file_tasks_mark_form,
        'comment_form': comment_form,
        'put_into_checking_group_form': put_into_checking_group_form,
    })


@school_view
@sistema.staff.only_staff
def check_group(request, group_name):
    qs = models.CheckingGroup.objects.filter(for_school=request.school, short_name=group_name)
    if not qs.exists():
        return Http404()

    _remove_old_checking_locks()

    checking_group = qs.first()

    with transaction.atomic():
        already_check_user = models.CheckingLock.objects.filter(
                locked_by=request.user,
                locked_user__userincheckinggroup__group=checking_group
        )
        if already_check_user.exists():
            user_for_checking = already_check_user.first().locked_user
        else:
            group_users = models.UserInCheckingGroup.objects.filter(group=checking_group,
                                                                    user__checking_locked__isnull=True)
            if not group_users.exists():
                return redirect('school:entrance:check', school_name=request.school.short_name)

            user_for_checking = group_users.first().user

            models.CheckingLock(locked_user=user_for_checking, locked_by=request.user).save()

    return check_user(request, user_for_checking, checking_group)


@school_view
@sistema.staff.only_staff
def enrolling_user(request, user_id):
    user_for_checking = get_object_or_404(user.models.User, id=user_id)
    _remove_old_checking_locks()
    # TODO: check for locks by current user, add button «Unlock»

    return check_user(request, user_for_checking)


@school_view
@sistema.staff.only_staff
def solution(request, solution_id):
    task_solution = get_object_or_404(models.EntranceExamTaskSolution, id=solution_id)

    if hasattr(task_solution, 'fileentranceexamtasksolution'):
        file_solution = task_solution.fileentranceexamtasksolution
        original_filename = file_solution.original_filename
        return respond_as_attachment(request, file_solution.solution, '%06d_%s' % (int(task_solution.id), original_filename))

    if hasattr(task_solution, 'programentranceexamtasksolution'):
        program_solution = task_solution.programentranceexamtasksolution
        return respond_as_attachment(request, program_solution.solution, '%06d' % int(task_solution.id))

    return HttpResponseNotFound()
