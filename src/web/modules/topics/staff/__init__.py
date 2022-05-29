import sistema.staff
import groups
import frontend.icons
import modules.entrance.groups as entrance_groups
import modules.topics.models as topics_models


@sistema.staff.register_staff_interface
class TopicsStaffInterface(sistema.staff.StaffInterface):
    def __init__(self, request):
        super().__init__(request)
        if hasattr(request.school, 'topicquestionnaire'):
            self._questionnaire = request.school.topicquestionnaire
            self._filled_questionnaire_count = (
                self._questionnaire.statuses.filter(
                    status=topics_models.UserQuestionnaireStatus.Status.FINISHED
                ).count()
            )

        self.is_entrance_admin = groups.is_user_in_group(
            request.user,
            entrance_groups.ADMINS,
            request.school
        )

    def get_sidebar_menu(self):
        if not self._questionnaire:
            return []
        if not self.is_entrance_admin:
            return []

        topics = sistema.staff.MenuItem(
            self.request,
            'Тематическая анкета',
            'school:topics:info',
            frontend.icons.FaIcon('bar-chart-o'),
            label=sistema.staff.MenuItemLabel(self._filled_questionnaire_count, 'system')
        )

        return [topics]
