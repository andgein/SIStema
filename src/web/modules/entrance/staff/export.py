import collections
import enum
import itertools

import xlsxwriter

from django.db.models import Count
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
import django.views

from modules.entrance import models
from modules.entrance import upgrades
import questionnaire.models
import modules.ejudge.models as ejudge_models
import modules.study_results.models as study_results_models
import schools.models
import sistema.staff
import users.models


class ExportCompleteEnrollingTable(django.views.View):
    class ColumnType(enum.Enum):
        PLAIN = 1
        MULTICOLUMN = 2
        URL = 3

    @method_decorator(sistema.staff.only_staff)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        enrollees = (
            users.models.User.objects
            .filter(entrance_statuses__school=request.school)
            .exclude(entrance_statuses__status=
                     models.EntranceStatus.Status.NOT_PARTICIPATED)
            .order_by('id')
        )

        columns = self.get_enrolling_columns(request, enrollees)

        ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(content_type=ct)
        response['Content-Disposition'] = "attachment; filename=enrolling.xlsx"

        book = xlsxwriter.Workbook(response, {'in_memory': True})
        sheet = book.add_worksheet('Поступление в ЛКШ')

        header_fmt = book.add_format({
            'bold': True,
            'text_wrap': True,
            'align': 'center',
        })
        cell_fmt = book.add_format({
            'text_wrap': True,
        })
        plain_header = (request.GET.get('plain_header') == 'true')
        for column in columns:
            column.header_format = header_fmt
            column.cell_format = cell_fmt
            column.plain_header = plain_header

        # Write header
        header_height = max(column.header_height for column in columns)
        irow, icol = 0, 0
        for column in columns:
            column.write(sheet, irow, icol, header_height=header_height)
            icol += column.width

        sheet.freeze_panes(1 if plain_header else header_height, 3)
        book.close()

        return response

    def get_enrolling_columns(self, request, enrollees):
        columns = []

        columns.append(LinkExcelColumn(
            name='id',
            cell_width=5,
            data=[user.id for user in enrollees],
            data_urls=[
                request.build_absolute_uri(django.urls.reverse(
                    'school:entrance:enrolling_user',
                    args=(request.school.short_name, user.id)))
                for user in enrollees
            ],
        ))

        columns.append(LinkExcelColumn(
            name='Фамилия',
            data=[user.profile.last_name for user in enrollees],
            data_urls=[getattr(user.profile.poldnev_person, 'url', '')
                       for user in enrollees],
        ))

        columns.append(PlainExcelColumn(
            name='Имя',
            data=[user.profile.first_name for user in enrollees],
        ))

        columns.append(PlainExcelColumn(
            name='Отчество',
            data=[user.profile.middle_name for user in enrollees],
        ))

        columns.append(PlainExcelColumn(
            name='Пол',
            data=['жм'[user.profile.sex == users.models.UserProfile.Sex.MALE]
                  for user in enrollees],
        ))

        columns.append(PlainExcelColumn(
            name='Город',
            data=[user.profile.city for user in enrollees],
        ))

        columns.append(PlainExcelColumn(
            name='Класс',
            cell_width=7,
            data=[user.profile.get_class() for user in enrollees],
        ))

        columns.append(PlainExcelColumn(
            name='Школа',
            data=[user.profile.school_name for user in enrollees],
        ))

        if self.question_exists(request.school, 'entrance_reason'):
            columns.append(PlainExcelColumn(
                name='Основание для поступления',
                data=self.get_choice_question_for_users(
                    request.school, enrollees, 'entrance_reason'),
            ))

        if self.question_exists(request.school, 'previous_parallels'):
            columns.append(PlainExcelColumn(
                name='История',
                data=self.get_history_for_users(request.school, enrollees),
            ))

        columns.append(PlainExcelColumn(
            name='История (poldnev.ru)',
            data=self.get_poldnev_history_for_users(enrollees),
        ))

        previous_school = schools.models.School.objects.get(short_name='2017')
        columns.append(PlainExcelColumn(
            name='Параллель',
            data=self.get_real_parallel_for_users(enrollees, previous_school),
        ))

        if self.question_exists(request.school, 'main_langauge'):
            columns.append(PlainExcelColumn(
                name='Язык (основной)',
                data=self.get_text_question_for_users(
                    request.school, enrollees, 'main_langauge'),
            ))

        if self.question_exists(request.school, 'travel_pasport'):
            columns.append(PlainExcelColumn(
                name='Загран',
                data=self.get_choice_question_for_users(
                    request.school, enrollees, 'travel_pasport'),
            ))

        if self.question_exists(request.school, 'visa'):
            columns.append(PlainExcelColumn(
                name='Виза',
                data=self.get_choice_question_for_users(
                    request.school, enrollees, 'visa'),
            ))

        if self.question_exists(request.school, 'visa_expiration'):
            columns.append(PlainExcelColumn(
                name='Срок действия визы',
                data=self.get_text_question_for_users(
                    request.school, enrollees, 'visa_expiration'),
            ))

        if self.question_exists(request.school, 'fingerprints'):
            columns.append(PlainExcelColumn(
                name='Отпечатки',
                data=self.get_choice_question_for_users(
                    request.school, enrollees, 'fingerprints'),
            ))

        if hasattr(request.school, 'entrance_exam'):
            columns.append(PlainExcelColumn(
                name='Языки ОК\'ов',
                data=self.get_ok_languages_for_users(request.school, enrollees),
            ))

            columns.append(PlainExcelColumn(
                name='Уровень',
                data=self.get_entrance_level_for_users(request.school,
                                                       enrollees),
            ))

            columns.append(PlainExcelColumn(
                name='Апгрейд',
                data=self.get_max_upgrade_for_users(request.school, enrollees),
            ))

            columns.append(PlainExcelColumn(
                name='Группы проверки',
                data=self.get_checking_groups_for_users(request.school,
                                                        enrollees),
            ))

            file_tasks = (
                models.FileEntranceExamTask.objects
                .annotate(entrance_levels_count=Count('entrance_levels'))
                .filter(exam__school=request.school,
                        entrance_levels_count__gt=0)
                .order_by('order')
            )
            if file_tasks.exists():
                subcolumns = [
                    PlainExcelColumn(
                        name='{}: {}'.format(task.id, task.title),
                        cell_width=5,
                        data=self.get_file_task_score_for_users(task, enrollees)
                    )
                    for task in file_tasks
                ]
                columns.append(ExcelMultiColumn(name='Теория',
                                                subcolumns=subcolumns))

            program_tasks = (
                models.ProgramEntranceExamTask.objects
                .annotate(entrance_levels_count=Count('entrance_levels'))
                .filter(exam__school=request.school,
                        entrance_levels_count__gt=0)
                .order_by('order')
            )
            if program_tasks.exists():
                subcolumns = [
                    PlainExcelColumn(
                        name='{}: {}'.format(task.id, task.title),
                        cell_width=5,
                        data=self.get_program_task_score_for_users(task,
                                                                   enrollees)
                    )
                    for task in program_tasks
                ]
                columns.append(ExcelMultiColumn(name='Практика',
                                                subcolumns=subcolumns))

            # TODO(artemtab): set of metrics to show shouldn't be hardcoded, but
            #     defined for each school/exam somewhere in the database.
            metrics = (models.EntranceUserMetric.objects
                       .filter(exam__school=request.school,
                               name__in=["C'", "C", "B'", "B", "A'", "A"])
                       .order_by('name'))
            if metrics.exists():
                subcolumns = [
                    PlainExcelColumn(
                        name=metric.name,
                        cell_width=5,
                        data=list(metric.values_for_users(enrollees))
                    )
                    for metric in metrics
                ]
                columns.append(ExcelMultiColumn(name='Баллы',
                                                subcolumns=subcolumns))

        if self.question_exists(request.school, 'want_to_session'):
            columns.append(PlainExcelColumn(
                name='Смена',
                data=self.get_choice_question_for_users(
                    request.school, enrollees, 'want_to_session'),
            ))

        if self.question_exists(request.school, 'other_session'):
            columns.append(PlainExcelColumn(
                name='Другая смена',
                data=self.get_other_session_for_users(request.school,
                                                      enrollees),
            ))

        entrance_status_by_user_id = self.get_entrance_status_by_user_id(
            request.school, enrollees)
        status_repr = {
            models.EntranceStatus.Status.NOT_PARTICIPATED: '!',
            models.EntranceStatus.Status.AUTO_REJECTED: 'ТО',
            models.EntranceStatus.Status.NOT_ENROLLED: 'X',
            models.EntranceStatus.Status.ENROLLED: '+',
            models.EntranceStatus.Status.PARTICIPATING: '',
        }
        columns.append(ExcelMultiColumn(
            name='Итог',
            subcolumns=[
                PlainExcelColumn(
                    name='Параллель',
                    cell_width=8,
                    data=[getattr(entrance_status_by_user_id[user.id].parallel,
                                  'name',
                                  '')
                          for user in enrollees],
                ),
                PlainExcelColumn(
                    name='Смена',
                    cell_width=7,
                    data=[getattr(entrance_status_by_user_id[user.id].session,
                                  'name',
                                  '')
                          for user in enrollees],
                ),
                PlainExcelColumn(
                    name='Статус',
                    cell_width=5,
                    data=[
                        status_repr.get(
                            entrance_status_by_user_id[user.id].status)
                        for user in enrollees
                    ],
                ),
                PlainExcelColumn(
                    name='Комментарий',
                    data=[entrance_status_by_user_id[user.id].public_comment
                          for user in enrollees],
                ),
                PlainExcelColumn(
                    name='Приватный комментарий',
                    data=[entrance_status_by_user_id[user.id].private_comment
                          for user in enrollees],
                ),
            ],
        ))

        # TODO(artemtab): we need some way to define for each school the
        #     previous ones in the database.
        columns.append(ExcelMultiColumn(
            name='',
            subcolumns=[
                PlainExcelColumn(
                    name='Оценки 2017.Зима',
                    cell_width=7,
                    data=self.get_marks_for_users('2017.winter', enrollees),
                ),
                PlainExcelColumn(
                    name='Оценки 2017',
                    cell_width=7,
                    data=self.get_marks_for_users('2017', enrollees),
                ),
            ],
        ))

        columns.append(PlainExcelColumn(
            name='Комментарии 2017',
            cell_width=30,
            data=self.get_study_comments_for_users('2017', enrollees),
        ))

        if (self.question_exists(request.school, 'informatics_olympiads') and
                self.question_exists(request.school, 'math_olympiads')):
            columns.append(ExcelMultiColumn(
                name='Олимпиады',
                subcolumns=[
                    PlainExcelColumn(
                        name='Информатика',
                        cell_width=30,
                        data=self.get_text_question_for_users(
                            request.school, enrollees, 'informatics_olympiads'),
                    ),
                    PlainExcelColumn(
                        name='Математика',
                        cell_width=30,
                        data=self.get_text_question_for_users(
                            request.school, enrollees, 'math_olympiads'),
                    ),
                ],
            ))

        return columns

    def get_history_for_users(self, school, enrollees):
        previous_parallel_answers = (
            questionnaire.models.QuestionnaireAnswer.objects
            .filter(user__in=enrollees,
                    questionnaire__school=school,
                    question_short_name='previous_parallels')
            .order_by('user__id', 'answer')
        )
        answer_variant_by_id = self.get_answer_variant_by_id(school)
        history_by_user = {
            user: ', '.join(answer_variant_by_id[ans.answer].text
                            for ans in answers)
            for user, answers in itertools.groupby(previous_parallel_answers,
                                                   lambda ans: ans.user)
        }
        return [history_by_user.get(user, '') for user in enrollees]

    def get_poldnev_history_for_users(self, enrollees):
        enrollees_with_history = enrollees.prefetch_related(
            'profile__poldnev_person__history_entries__study_group__parallel')
        history_by_user = {}
        for user in enrollees_with_history:
            if not user.profile or not user.profile.poldnev_person:
                continue
            history_by_user[user] = ', '.join(
                entry.study_group.parallel.name
                for entry in user.profile.poldnev_person.history_entries.all()
                if entry.study_group
                if not entry.role # Student
            )
        return [history_by_user.get(user, '') for user in enrollees]

    def get_real_parallel_for_users(self, enrollees, school):
        real_parallels = []
        for user in enrollees:
            participation = (user.school_participations
                             .filter(school=school)
                             .first())
            real_parallels.append('' if participation is None
                                  else participation.parallel.name)
        return real_parallels

    def get_entrance_level_for_users(self, school, enrollees):
        return [upgrades.get_base_entrance_level(school, user).name
                for user in enrollees]

    def get_max_upgrade_for_users(self, school, enrollees):
        issued_upgrades = (
            models.EntranceLevelUpgrade.objects
            .filter(user__in=enrollees,
                    upgraded_to__school=school)
            .order_by('upgraded_to__order')
        )
        max_level_by_user = {upgrade.user: upgrade.upgraded_to.name
                             for upgrade in issued_upgrades}
        return [max_level_by_user.get(user, '') for user in enrollees]

    def get_other_session_for_users(self, school, enrollees):
        other_session_answers = (
            questionnaire.models.QuestionnaireAnswer.objects
            .filter(user__in=enrollees,
                    questionnaire__school=school,
                    question_short_name='other_session')
        )
        other_session_by_user = {
            answer.user: 'Да' if answer.answer == 'True' else 'Нет'
            for answer in other_session_answers
        }
        return [other_session_by_user.get(user, '') for user in enrollees]

    def get_marks_for_users(self, school_short_name, enrollees):
        results = (
            study_results_models.StudyResult.objects
            .filter(school_participant__user__in=enrollees,
                    school_participant__school__short_name=school_short_name)
        )
        marks_by_user_id = {
            result.school_participant.user_id: '{} / {}'.format(
                result.theory, result.practice)
            for result in results}
        return [marks_by_user_id.get(user.id, '') for user in enrollees]

    def get_study_comments_for_users(self, school_short_name, enrollees):
        comments = (
            study_results_models.AbstractComment.objects
            .filter(study_result__school_participant__user__in=enrollees,
                    study_result__school_participant__school__short_name=
                    school_short_name)
            .select_related('study_result__school_participant')
        )
        comments_by_user_id = collections.defaultdict(list)
        for comment in comments:
            user_id = comment.study_result.school_participant.user_id
            comments_by_user_id[user_id].append(comment)
        return [
            '\n'.join('[{}] {}'.format(comment.verbose_type(), comment.comment)
                      for comment in comments_by_user_id[user.id])
            for user in enrollees
        ]

    def get_checking_groups_for_users(self, school, enrollees):
        groups_by_user_id = collections.defaultdict(list)
        for checking_group in school.entrance_checking_groups:
            group_user_ids = checking_group.group.user_ids
            for user_id in group_user_ids:
                groups_by_user_id[user_id].append(checking_group)

        return [', '.join(group.name for group in groups_by_user_id[user.id])
                for user in enrollees]

    def get_entrance_status_by_user_id(self, school, enrollees):
        entrance_statuses = (
            models.EntranceStatus.objects
            .filter(school=school, user__in=enrollees)
            .select_related('session', 'parallel')
        )
        return {entrance_status.user_id: entrance_status
                for entrance_status in entrance_statuses}

    def get_ok_languages_for_users(self, school, enrollees):
        OK = ejudge_models.CheckingResult.Result.OK
        ok_solutions = (
            models.ProgramEntranceExamTaskSolution.objects
            .filter(task__exam__school=school,
                    user__in=enrollees,
                    ejudge_queue_element__submission__result__result=OK)
            .select_related('language')
        )
        languages_by_user_id = collections.defaultdict(set)
        for solution in ok_solutions:
            languages_by_user_id[solution.user_id].add(solution.language.name)
        return ['\n'.join(sorted(languages_by_user_id[user.id]))
                for user in enrollees]

    def get_file_task_score_for_users(self, task, enrollees):
        checked_solutions = (
            models.CheckedSolution.objects
            .filter(solution__user__in=enrollees, solution__task=task)
            .order_by('created_at')
            .select_related('solution__user')
        )
        # If there are duplicate keys in dictionary comprehensions the last
        # always wins. That way we will use the score from the last available
        # check.
        last_score_by_user_id = {
            checked_solution.solution.user.id: checked_solution.score
            for checked_solution in checked_solutions
        }
        return [last_score_by_user_id.get(user.id, '') for user in enrollees]

    def get_program_task_score_for_users(self, task, enrollees):
        OK = ejudge_models.CheckingResult.Result.OK
        solved_user_ids = set(
            models.ProgramEntranceExamTaskSolution.objects
            .filter(user__in=enrollees,
                    task=task,
                    ejudge_queue_element__submission__result__result=OK)
            .values_list('user_id', flat=True)
        )
        return [('1' if user.id in solved_user_ids else '')
                for user in enrollees]

    def get_text_question_for_users(self, school, enrollees, short_name):
        answers = (
            questionnaire.models.QuestionnaireAnswer.objects
            .filter(user__in=enrollees,
                    questionnaire__school=school,
                    question_short_name=short_name)
        )
        answer_by_user = {answer.user: answer.answer
                          for answer in answers}
        return [answer_by_user.get(user, '') for user in enrollees]

    def get_choice_question_for_users(self, school, enrollees, short_name):
        answers = (
            questionnaire.models.QuestionnaireAnswer.objects
            .filter(user__in=enrollees,
                    questionnaire__school=school,
                    question_short_name=short_name)
        )
        answer_variant_by_id = self.get_answer_variant_by_id(school)
        answer_by_user = {
            answer.user: answer_variant_by_id[answer.answer].text
            for answer in answers
        }
        return [answer_by_user.get(user, '') for user in enrollees]

    def question_exists(self, school, question_short_name):
        return (questionnaire.models.AbstractQuestionnaireQuestion.objects
                .filter(short_name=question_short_name,
                        questionnaire__school_id=school.id)
                .exists())

    def get_answer_variant_by_id(self, school):
        variants = (
            questionnaire.models.ChoiceQuestionnaireQuestionVariant.objects
            .filter(question__questionnaire__school=school)
        )
        return {str(var.id): var for var in variants}


class ExcelColumn:
    def __init__(self, name='', plain_header=False):
        self.name = name
        self.plain_header = plain_header

    @property
    def width(self):
        return 1

    @property
    def header_height(self):
        return 1

    @cached_property
    def header_format(self):
        return None

    @cached_property
    def cell_format(self):
        return None

    def write_header(self, sheet, irow, icol, header_height=None):
        if self.plain_header or header_height == 1:
            sheet.write(irow, icol, self.name, self.header_format)
        else:
            sheet.merge_range(irow,
                              icol,
                              irow + header_height - 1,
                              icol,
                              self.name,
                              cell_format=self.header_format)
        return irow + (1 if self.plain_header else header_height)

    def write(self, sheet, irow, icol, header_height=None):
        return NotImplementedError()


class PlainExcelColumn(ExcelColumn):
    def __init__(self,
                 data=None,
                 cell_width=15,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = [] if data is None else data
        self.cell_width = cell_width

    def write(self, sheet, irow, icol, header_height=None):
        sheet.set_column(icol, icol, self.cell_width)

        irow = self.write_header(sheet, irow, icol, header_height)

        for i, value in enumerate(self.data):
            sheet.write(irow + i, icol, value, self.cell_format)


class LinkExcelColumn(PlainExcelColumn):
    def __init__(self, data_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_urls = self.data if data_urls is None else data_urls
        if len(self.data) != len(self.data_urls):
            raise ValueError()

    def write(self, sheet, irow, icol, header_height=None):
        sheet.set_column(icol, icol, self.cell_width)

        irow = self.write_header(sheet, irow, icol, header_height)

        for i, (value, url) in enumerate(zip(self.data, self.data_urls)):
            if url:
                sheet.write_url(irow + i, icol, url, string=str(value))
            else:
                sheet.write(irow + i, icol, value)


class ExcelMultiColumn(ExcelColumn):
    def __init__(self, subcolumns=None, *args, **kwargs):
        if not subcolumns:
            raise ValueError(
                'ExcelMultiColumn should have at least one subcolumn')
        self.subcolumns = subcolumns
        super().__init__(*args, **kwargs)

    @property
    def width(self):
        return sum(subcolumn.width for subcolumn in self.subcolumns)

    @property
    def header_height(self):
        return 1 + max(subcolumn.header_height
                       for subcolumn in self.subcolumns)

    def write(self, sheet, irow, icol, header_height=None):
        if not self.plain_header:
            if len(self.subcolumns) > 1:
                sheet.merge_range(irow,
                                  icol,
                                  irow,
                                  icol + self.width - 1,
                                  self.name,
                                  self.header_format)
            else:
                sheet.write(irow, icol, self.name, self.header_format)
            irow += 1

        for column in self.subcolumns:
            column.header_format = self.header_format
            column.write(sheet, irow, icol, header_height=header_height - 1)
            icol += column.width
