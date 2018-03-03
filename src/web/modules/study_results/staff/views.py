import django.shortcuts

import frontend.icons
import frontend.table
import groups.decorators
import modules.study_results.models as study_results_models
import sistema.staff
import users.models
from frontend.table.utils import A, TableDataSource
from modules.study_results.groups import STUDENT_COMMENTS_VIEWERS


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
        kwargs={'user_id': A('school_participant.user.id')})

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
            django.urls.reverse('school:study_results:study_results_data',
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
