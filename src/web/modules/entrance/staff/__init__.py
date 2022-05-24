import frontend.icons
import sistema.staff
from . import views
from .. import groups as entrance_groups
from .. import utils
import groups


@sistema.staff.register_staff_interface
class EntranceStaffInterface(sistema.staff.StaffInterface):
    def __init__(self, request):
        super().__init__(request)
        self._enrollees_count = \
            utils.get_enrolling_user_ids(request.school).count()

        self.is_entrance_admin = groups.is_user_in_group(
            request.user,
            entrance_groups.ADMINS,
            request.school
        )
        self.can_check = groups.is_user_in_group(
            request.user,
            entrance_groups.CAN_CHECK,
            request.school
        )

    def get_sidebar_menu(self):
        filled_an_application = sistema.staff.MenuItem(
            self.request,
            'Подавшие заявку',
            'school:entrance:enrolling',
            frontend.icons.FaIcon('envelope-o'),
            label=sistema.staff.MenuItemLabel(self._enrollees_count, 'system')
        )

        exam_tasks = sistema.staff.MenuItem(
            self.request,
            'Задания',
            '',
            frontend.icons.GlyphIcon('book')
        )

        exam_checking = sistema.staff.MenuItem(
            self.request,
            'Проверка',
            'school:entrance:check',
            frontend.icons.FaIcon('desktop')
        )

        exam_results = sistema.staff.MenuItem(
            self.request,
            'Результаты',
            'school:entrance:results',
            frontend.icons.FaIcon('rocket')
        )

        ejudge_stats = sistema.staff.MenuItem(
            self.request,
            'Статистика по практике',
            'school:ejudge:show_ejudge_stats',
            frontend.icons.GlyphIcon('equalizer')
        )

        exam = sistema.staff.MenuItem(
            self.request,
            'Вступительная',
            '',
            frontend.icons.FaIcon('columns'),
            children=[exam_tasks, exam_checking, ejudge_stats, exam_results]
        )

        items = []
        if self.is_entrance_admin:
            items.append(filled_an_application)
        if self.can_check:
            items.append(exam)

        return items
