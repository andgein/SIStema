import csv
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import django.db.transaction
import django.shortcuts
import django.urls
from django.http import HttpRequest, HttpResponse

import frontend.icons
import frontend.table
import groups.decorators
import modules.study_results.models as study_results_models
import schools.models
import sistema.uploads
import users.models
from frontend.table.utils import A, TableDataSource
from modules.study_results.groups import STUDENT_COMMENTS_VIEWERS, STUDENT_COMMENTS_EDITORS
from . import forms


class StudyResultsTable(frontend.table.Table):
    name = frontend.table.LinkColumn(
        accessor='school_participant.user.get_full_name',
        verbose_name='Имя',
        order_by=('school_participant.user.profile.last_name',
                  'school_participant.user.profile.first_name',
                  'school_participant.user.profile.middle_name'),
        search_in=('school_participant.user.profile.first_name',
                   'school_participant.user.profile.middle_name',
                   'school_participant.user.profile.last_name'),
        viewname='study_results:study_result_user',
        kwargs={'user_id': A('school_participant__user__id')})

    city = frontend.table.Column(
        accessor='school_participant.user.profile.city',
        verbose_name='Город',
        orderable=True,
        searchable=True)

    school_and_class = frontend.table.Column(
        accessor='school_participant.user.profile',
        verbose_name='Школа, класс',
        search_in='school_participant.user.profile.school_name')

    # TODO: filterable
    parallel = frontend.table.Column(
        accessor='school_participant.parallel.name',
        verbose_name='Параллель',
        orderable=True)

    # TODO: filterable
    theory = frontend.table.Column(
        accessor='theory',
        verbose_name='Теория',
        orderable=True)

    # TODO: filterable
    practice = frontend.table.Column(
        accessor='practice',
        verbose_name='Практика',
        orderable=True)

    comments = frontend.table.Column(
        accessor='comments',
        verbose_name='Комментарии')

    class Meta:
        icon = frontend.icons.FaIcon('envelope-o')
        title = 'Результаты обучения в школе'
        exportable = True

    def __init__(self, school, *args, **kwargs):
        qs = (study_results_models.StudyResult.objects
              .filter(school_participant__school=school)
              .select_related('school_participant')
              .prefetch_related('comments')
              .order_by('school_participant__parallel__name',
                        'school_participant__user__profile__last_name'))

        super().__init__(
            qs,
            django.urls.reverse('school:study_results:data',
                                args=[school.short_name]),
            *args, **kwargs)

    def render_school_and_class(self, value):
        parts = []
        if value.school_name:
            parts.append(value.school_name)
        if value.current_class is not None:
            parts.append(str(value.current_class) + ' класс')
        return ', '.join(parts)

    def render_comments(self, value):
        return ''.join('<p>' + str(comment) + '</p>' for comment in value.all())


@groups.decorators.only_for_groups(STUDENT_COMMENTS_VIEWERS)
def study_results(request):
    study_results_table = StudyResultsTable(request.school)
    frontend.table.RequestConfig(request).configure(study_results_table)
    return django.shortcuts.render(
        request, 'study_results/staff/study_results.html',
        {'study_results_table': study_results_table})


@groups.decorators.only_for_groups(STUDENT_COMMENTS_VIEWERS)
def study_results_data(request):
    table = StudyResultsTable(request.school)
    return TableDataSource(table).get_response(request)


@groups.decorators.only_for_groups(STUDENT_COMMENTS_VIEWERS)
def study_result_user(request, user_id):
    user = django.shortcuts.get_object_or_404(users.models.User, id=user_id)
    return django.shortcuts.render(
        request, 'study_results/staff/study_result_user.html',
        {'user_name': user.get_full_name()})


@dataclass
class UploadWarning:
    line_index: int
    line: dict
    message: str


def _find_parallel_by_parallel_or_group_name(
    parallel_name: str, parallels_by_name: Dict[str, schools.models.Parallel]
) -> Optional[schools.models.Parallel]:
    """
    Finds parallel by name of parallel or group. I.e. if group is 1A or A8,
    parallel "1" or "A" is returned.
    """
    if parallel_name in parallels_by_name:
        return parallels_by_name[parallel_name]

    if len(parallel_name) > 1 and parallel_name[:-1] in parallels_by_name:
        return parallels_by_name[parallel_name[:-1]]

    return None


@django.db.transaction.atomic
def _upload_study_results(
    school: schools.models.School, form: forms.UploadStudyResultsForm,
    saved_file: str, created_by: users.models.User,
) -> Tuple[int, List[UploadWarning]]:
    warnings: List[UploadWarning] = []
    parallels_by_name = {
        parallel.name: parallel for parallel in school.parallels.all()
    }
    with open(saved_file, 'r') as opened_file:
        reader = csv.DictReader(opened_file)
        line_index = None
        for line_index, line in enumerate(reader, start=1):
            try:
                user_id = line[form.cleaned_data['user_id_field_name']]
                user = users.models.User.objects.filter(id=user_id).first()
                if user is None:
                    warnings.append(
                        UploadWarning(line_index, line, f"Нет пользователя с айди {user_id}")
                    )
                    continue

                parallel_name = line[form.cleaned_data['parallel_field_name']]
                parallel = _find_parallel_by_parallel_or_group_name(
                    parallel_name, parallels_by_name
                )
                if not parallel:
                    warnings.append(
                        UploadWarning(line_index, line, f"Неизвестная параллель «{parallel_name}». "
                                                        f"Допустимые параллели: {list(parallels_by_name.keys())}")
                    )
                    continue
                theory = line[form.cleaned_data['theory_field_name']].strip()
                if not theory:
                    theory = "N/A"
                practice = line[form.cleaned_data['practice_field_name']].strip()
                if not practice:
                    practice = "N/A"

                participant, _ = schools.models.SchoolParticipant.objects.get_or_create(
                    school=school,
                    user=user,
                    defaults={
                        'parallel': parallel,
                    }
                )
                if participant.parallel != parallel:
                    warnings.append(
                        UploadWarning(
                            line_index, line,
                            f"Для школьника {user.get_full_name()} "
                            f"уже была установлена параллель {participant.parallel.name}, "
                            f"поменялась на {parallel.name}"
                        )
                    )
                    participant.parallel = parallel
                    participant.save()

                evaluation = study_results_models.StudyResult.Evaluation
                try:
                    evaluation.get_choice(theory)
                    evaluation.get_choice(practice)
                except KeyError as e:
                    warnings.append(UploadWarning(
                        line_index, line, f"Неизвестная оценка «{e.args[0]}». "
                                          f"Допустимые оценки: {list(evaluation.labels.values())}"
                    ))
                    continue

                study_result, _ = study_results_models.StudyResult.objects.update_or_create(
                    school_participant=participant,
                    defaults={
                        'theory': theory,
                        'practice': practice,
                    }
                )

                comments = {
                    'study_comment_field_name': study_results_models.StudyComment,
                    'social_comment_field_name': study_results_models.SocialComment,
                    'as_winter_participant_field_name': study_results_models.AsWinterParticipantComment,
                    'next_year_field_name': study_results_models.NextYearComment,
                    'as_teacher_field_name': study_results_models.AsTeacherComment,
                    'after_winter_field_name': study_results_models.AfterWinterComment,
                }
                for comment_field_name, comment_class in comments.items():
                    if form.cleaned_data[comment_field_name] and line[form.cleaned_data[comment_field_name]]:
                        comment_class.objects.get_or_create(
                            study_result=study_result,
                            defaults={
                                'comment': line[form.cleaned_data[comment_field_name]],
                                'created_by': created_by,
                            }
                        )
            except KeyError as e:
                warnings.append(UploadWarning(
                    line_index, line, f"Не найдена колонка «{e.args[0]}»"
                ))
            except Exception as e:
                warnings.append(UploadWarning(
                    line_index, line, f"Ошибка: {e}"
                ))

        if line_index is None:
            warnings.append(UploadWarning(
                1, {}, "Пустой файл"
            ))

    return line_index, warnings


@groups.decorators.only_for_groups(STUDENT_COMMENTS_EDITORS)
def upload_study_results(request: HttpRequest) -> HttpResponse:
    records_count = None
    warnings: List[UploadWarning] = []
    if request.method == 'POST':
        form = forms.UploadStudyResultsForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            saved_file = sistema.uploads.save_file(file, 'study-results', 'csv')
            try:
                records_count, warnings = _upload_study_results(request.school, form, saved_file, request.user)
            except Exception as e:
                form.add_error('file', f'Не удалось прочитать CSV-файл. Питоновская ошибка: {e}.')
    else:
        form = forms.UploadStudyResultsForm()

    return django.shortcuts.render(
        request, 'study_results/staff/upload_study_results.html',
        {
            'school': request.school,
            'form': form,
            'uploaded_records_count': records_count,
            'uploading_warnings': warnings,
        }
    )
