from typing import Iterable

import django.urls
import django.views
import xlsxwriter
from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe

import frontend.icons
import frontend.table
import sistema.staff
import users.models
from frontend.table import A
from groups import models
from sistema.export import ExcelColumn, PlainExcelColumn, LinkExcelColumn


class GroupMembersTable(frontend.table.Table):
    index = frontend.table.IndexColumn(verbose_name='')

    user_id = frontend.table.Column(
        accessor='id',
        verbose_name='ID',
        order_by=('id', ),
        search_in=('id', ),
    )

    name = frontend.table.Column(
        accessor='get_full_name_starting_with_last_name',
        verbose_name='Имя',
        order_by=('profile.last_name', 'profile.first_name'),
        search_in=('profile.first_name', 'profile.last_name')
    )

    city = frontend.table.Column(
        accessor='profile__city',
        orderable=True,
        searchable=True,
        verbose_name='Город'
    )

    klass = frontend.table.Column(
        accessor='profile__get_class',
        verbose_name='Класс',
    )

    def __init__(self, group, *args, **kwargs):
        qs = group.users.order_by(
            'profile__last_name',
            'profile__first_name',
        ).select_related('profile')

        data_url = django.urls.reverse(
            'school:groups:members_data',
            args=[group.school.short_name, group.short_name]
        )

        super().__init__(qs, data_url, *args, **kwargs)

    class Meta:
        icon = frontend.icons.FaIcon('user')
        title = 'Участники группы'
        pagination = (100, 500)


@sistema.staff.only_staff
def group_info(request, group_name):
    group = get_object_or_404(
        models.AbstractGroup,
        school=request.school,
        short_name=group_name
    )

    if not group.can_user_list_members(request.user):
        return HttpResponseNotFound()

    table = GroupMembersTable(group)
    frontend.table.RequestConfig(request).configure(table)

    return render(request, 'groups/staff/group.html', {
        'group': group,
        'table': table
    })


@sistema.staff.only_staff
def members_data(request, group_name):
    group = get_object_or_404(
        models.AbstractGroup,
        school=request.school,
        short_name=group_name
    )

    if not group.can_user_list_members(request.user):
        return HttpResponseNotFound()

    table = GroupMembersTable(group)
    return frontend.table.TableDataSource(table).get_response(request)


class GroupsListTable(frontend.table.Table):
    index = frontend.table.IndexColumn(verbose_name='')

    name = frontend.table.TemplateColumn(
        template_name='groups/staff/_groups_list_group_name.html',
        # TODO (andgein): it's a hack to retrieve current object as an accessor.
        # Null and empty accessor don't work, but I don't know why
        accessor='abstractgroup_ptr__get_real_instance',
        verbose_name='Имя',
        orderable=True,
        order_by='name',
        searchable=True,
        search_in='name'
    )

    description = frontend.table.Column(
        accessor='description',
        searchable=True,
        verbose_name='Описание'
    )

    members_count = frontend.table.Column(
        # TODO (andgein): it's a hack to retrieve current object as an accessor.
        # Null and empty accessor don't work, but I don't know why
        accessor='abstractgroup_ptr__get_real_instance',
        verbose_name='Участников',
    )

    export_link = frontend.table.LinkColumn(
        accessor='abstractgroup_ptr__get_real_instance',
        verbose_name='Скачать XLSX',
        viewname='school:groups:export_group',
        args=[A('school__short_name'), A('short_name')],
    )

    def __init__(self, school, user, *args, **kwargs):
        visible_group_ids = []
        school_groups = models.AbstractGroup.objects.filter(school=school)
        for group in school_groups:
            # Now following line produces extra query for each group
            # TODO (andgein): make one smart query to database to fetch
            # all groups visible to current user
            if group.can_user_list_members(user):
                visible_group_ids.append(group.id)

        qs = (
            models.AbstractGroup.objects
                .select_related('school')
                .filter(id__in=visible_group_ids).order_by(
                    'name',
                    'description',
                )
        )

        data_url = django.urls.reverse(
            'school:groups:list_data',
            args=[school.short_name]
        )

        super().__init__(qs, data_url, *args, **kwargs)

    class Meta:
        icon = frontend.icons.FaIcon('group')
        title = 'Группы'
        pagination = False

    def render_members_count(self, value):
        return str(len(value.user_ids))

    def render_export_link(self, value):
        return mark_safe('<span class="fa fa-download"></span>')


@sistema.staff.only_staff
def groups_list(request):
    table = GroupsListTable(request.school, request.user)
    frontend.table.RequestConfig(request).configure(table)

    return render(request, 'groups/staff/groups.html', {
        'school': request.school,
        'table': table
    })


@sistema.staff.only_staff
def groups_list_data(request):
    table = GroupsListTable(request.school, request.user)
    return frontend.table.TableDataSource(table).get_response(request)


class ExportGroup(django.views.View):
    @method_decorator(sistema.staff.only_staff)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, group_name: str):
        group = get_object_or_404(
            models.AbstractGroup,
            school=request.school,
            short_name=group_name
        )

        if not group.can_user_list_members(request.user):
            return HttpResponseNotFound()

        members = list(group.users.order_by('id').select_related('profile'))

        columns = self._get_columns(request, members)

        ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response = HttpResponse(content_type=ct)
        response['Content-Disposition'] = f"attachment; filename={group.short_name}.xlsx"

        book = xlsxwriter.Workbook(response, {'in_memory': True})
        # 31 is max length of Excel worksheet's name.
        # Also some characters are forbidden in worksheet names, but let's ignore it for now.
        sheet = book.add_worksheet(f'{group.school.name}. {group.name}'[:31])

        # TODO (andgein): It's a copy-paste from ExportCompleteEnrollingTable, clean it up?
        header_fmt = book.add_format({
            'bold': True,
            'text_wrap': True,
            'align': 'center',
        })
        cell_fmt = book.add_format({
            'text_wrap': True,
        })
        plain_header = (request.GET.get('plain_header') != 'false')
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

    def _get_columns(self, request, members: Iterable[users.models.User]) -> Iterable[ExcelColumn]:
        columns = []

        columns.append(LinkExcelColumn(
            name='id',
            cell_width=5,
            data=[user.id for user in members],
            data_urls=[
                request.build_absolute_uri(django.urls.reverse(
                    'school:entrance:enrolling_user',
                    args=(request.school.short_name, user.id)))
                for user in members
            ],
        ))

        columns.append(LinkExcelColumn(
            name='Фамилия',
            data=[user.profile.last_name if hasattr(user, 'profile') else '' for user in members],
            data_urls=[getattr(user.profile.poldnev_person, 'url', '') if hasattr(user, 'profile') else ''
                       for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Имя',
            data=[user.profile.first_name if hasattr(user, 'profile') else '' for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Отчество',
            data=[user.profile.middle_name if hasattr(user, 'profile') else '' for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Пол',
            data=['жм'[user.profile.sex == users.models.UserProfile.Sex.MALE] if hasattr(user, 'profile') else ''
                  for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Город',
            data=[user.profile.city if hasattr(user, 'profile') else '' for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Класс',
            cell_width=7,
            data=[user.profile.get_class() if hasattr(user, 'profile') else '' for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Школа',
            data=[user.profile.school_name if hasattr(user, 'profile') else '' for user in members],
        ))

        columns.append(PlainExcelColumn(
            name='Емэйл',
            data=[user.email for user in members]
        ))

        return columns
