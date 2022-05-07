import groups
import sistema.staff
import frontend.icons

from .. import groups as study_results_groups


@sistema.staff.register_staff_interface
class EntranceStaffInterface(sistema.staff.StaffInterface):
    def __init__(self, request):
        super().__init__(request)

        self.student_comments_viewer = groups.is_user_in_group(
            request.user,
            study_results_groups.STUDENT_COMMENTS_VIEWERS,
            request.school
        )
        self.student_comments_editor = groups.is_user_in_group(
            request.user,
            study_results_groups.STUDENT_COMMENTS_EDITORS,
            request.school
        )

    def get_sidebar_menu(self):
        view_study_results = sistema.staff.MenuItem(
            self.request,
            'Просмотр',
            'school:study_results:view',
            frontend.icons.FaIcon('sort-numeric-asc'),
        )

        upload_study_results = sistema.staff.MenuItem(
            self.request,
            'Загрузка',
            'school:study_results:upload',
            frontend.icons.FaIcon('upload'),
        )

        children = []
        if self.student_comments_viewer:
            children.append(view_study_results)
        if self.student_comments_editor:
            children.append(upload_study_results)

        study_results = sistema.staff.MenuItem(
            self.request,
            'Результаты обучения',
            '',
            frontend.icons.FaIcon('trophy'),
            children=children
        )

        return [study_results] if children else []
