from django.apps import AppConfig, apps
from django.db import transaction
from django.db.models.signals import post_save


class GroupsConfig(AppConfig):
    name = 'groups'

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self._auto_access = []
        self._auto_members = []

    def ready(self):
        try:
            self._ensure_all_groups_exist_and_configured()
            self._set_hook_for_new_school()
        except Exception as e:
            if self.is_db_init_error(e):
                print('Skipping groups creating because db is not ready yet')
            else:
                raise

    @staticmethod
    def is_db_init_error(e):
        return "doesn't exist" in str(e) or \
               'no such table:' in str(e) or \
               'does not exist' in str(e)

    def _ensure_all_groups_exist_and_configured(self):
        self._auto_members.clear()
        self._auto_access.clear()

        for app_config in apps.get_app_configs():
            if not hasattr(app_config, 'sistema_groups'):
                continue

            groups = app_config.sistema_groups
            for group_name, group_spec in groups.items():
                self._ensure_group_exists(group_name, group_spec)

        for group, auto_members in self._auto_members:
            self._set_auto_members(group, auto_members)
        for group, auto_access in self._auto_access:
            self._set_auto_access(group, auto_access)

    @transaction.atomic
    def _ensure_group_exists(self, group_name, group_spec):
        system_wide = group_spec.get('system_wide', False)
        if system_wide:
            self._ensure_system_wide_group_exists(group_name, group_spec)
        else:
            self._ensure_school_group_exists(group_name, group_spec)

    def _ensure_system_wide_group_exists(self, group_name, group_params):
        # You can't import models on module level:
        # https://docs.djangoproject.com/en/1.11/ref/applications/#django.apps.AppConfig.ready
        from groups.models import ManuallyFilledGroup

        group = ManuallyFilledGroup.objects.filter(
            school__isnull=True,
            short_name=group_name
        ).first()
        if group is None:
            self._create_system_wide_group(group_name, group_params)
        else:
            self._update_group(group, group_params)

    def _ensure_school_group_exists(self, group_name, group_spec):
        from schools.models import School
        from groups.models import ManuallyFilledGroup

        for school in School.objects.all():
            group = ManuallyFilledGroup.objects.filter(
                school=school,
                short_name=group_name
            ).first()
            if group is None:
                self._create_group(school, group_name, group_spec)
            else:
                self._update_group(group, group_spec)

    def _create_system_wide_group(self, group_name, group_spec):
        self._create_group(None, group_name, group_spec)

    def _create_group(self, school, group_name, group_spec):
        from groups.models import ManuallyFilledGroup

        group = ManuallyFilledGroup.objects.create(
            school=school,
            short_name=group_name,
            name=group_spec.get('name', ''),
            description=group_spec.get('description', ''),
            created_by=None,
            can_be_deleted=False,
        )

        self._auto_members.append((group, group_spec.get('auto_members', [])))
        self._auto_access.append((group, group_spec.get('auto_access', {})))

        print('Group #%d [%s] «%s» has been created for school %s' % (
            group.id,
            group.short_name,
            group.name,
            group.school
        ))

    def _update_group(self, group, group_params):
        group.name = group_params.get('name', '')
        group.description = group_params.get('description', '')
        group.created_by = None
        group.can_be_deleted = False
        self._auto_members.append((group, group_params.get('auto_members', [])))
        self._auto_access.append((group, group_params.get('auto_access', {})))
        group.save()

    def _set_auto_members(self, group, auto_members):
        from groups.models import ManuallyFilledGroup, GroupInGroupMembership

        for member_group_name in auto_members:
            member_group = ManuallyFilledGroup.objects.filter(
                school=group.school, short_name=member_group_name
            ).first()
            if member_group is None:
                raise LookupError(
                    'Can\'t find group %s for settings auto_member in %s' % (
                        member_group_name, str(group)
                    ))

            GroupInGroupMembership.objects.update_or_create(
                group=group,
                member=member_group,
                defaults={
                    'added_by': None,
                }
            )

    def _set_auto_access(self, group, auto_access):
        from groups.models import ManuallyFilledGroup, GroupAccessForGroup, GroupAccess

        access_type_by_name = {
            'admin': GroupAccess.Type.ADMIN,
            'list_members': GroupAccess.Type.LIST_MEMBERS,
            'edit_members': GroupAccess.Type.EDIT_MEMBERS,
        }

        for access_group_name, access_group_access_type in auto_access.items():
            if access_group_access_type not in access_type_by_name:
                raise ValueError(
                    'Invalid access_type in sistema_groups '
                    'for auto_accessed group %s: %s' % (
                        access_group_name,
                        access_group_access_type,
                    ))

            access_type = access_type_by_name[access_group_access_type]

            access_group = ManuallyFilledGroup.objects.filter(
                school=group.school, short_name=access_group_name
            ).first()
            if access_group is None:
                raise LookupError(
                    'Can\'t find group %s for settings auto_access' % (
                        access_group_name,
                    ))

            GroupAccessForGroup.objects.update_or_create(
                to_group=group,
                group=access_group,
                defaults={
                    'created_by': None,
                    'access_type': access_type,
                }
            )

    def _set_hook_for_new_school(self):
        import schools.models
        post_save.connect(
            self._on_new_school,
            sender=schools.models.School
        )

    def _on_new_school(self, **kwargs):
        if kwargs.get('raw'):
            # Ignore "loaddata" operations which is marked by "raw" keyword.
            # See https://stackoverflow.com/questions/3499791/how-do-i-prevent-fixtures-from-conflicting-with-django-post-save-signal-code
            # and https://code.djangoproject.com/ticket/8399
            return

        # Call initializing method again for creating groups for the new school
        self._ensure_all_groups_exist_and_configured()
