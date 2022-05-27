import collections

import djchoices
import polymorphic.models
from django.db import models
from django.utils.functional import cached_property

from sistema.cache import cache
import schools.models
import users.models


class AbstractGroup(polymorphic.models.PolymorphicModel):
    school = models.ForeignKey(
        schools.models.School,
        null=True,
        blank=True,
        related_name='groups',
        on_delete=models.CASCADE,
    )

    created_by = models.ForeignKey(
        users.models.User,
        null=True,
        blank=True,
        related_name='created_groups',
        on_delete=models.CASCADE,
        help_text='Создатель группы. Не может никогда измениться и '
                  'всегда имеет полные права на группу.'
                  'None, если владелец группы — система'
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. '
                  'Лучше обойтись латинскими буквами, цифрами и подчёркиванием',
        db_index=True,
    )

    name = models.CharField(
        max_length=60,
        help_text='Покороче, используется на метках'
    )

    description = models.TextField(help_text='Подлинее, подробное описание')

    can_be_deleted = models.BooleanField(
        default=True,
        help_text='Системные группы не могут быть удалены',
    )

    list_members_to_everyone = models.BooleanField(
        default=False,
        help_text='Видно ли всем участие других в этой группе',
    )

    class Meta:
        unique_together = ('short_name', 'school')
        verbose_name = 'group'

    def __str__(self):
        result = 'Группа «%s»' % self.name
        if self.school is not None:
            result += ' для ' + str(self.school)
        return result

    def is_user_in_group(self, user):
        """
        You can override this method in subclass.
        By default, it calls overridden self.user_ids.
        Be careful: this approach can be slow on large groups.
        :return: True if user is in group and False otherwise.
        """
        return user.id in self.user_ids

    @property
    def users(self):
        """
        You can override this method in subclass. By default it calls overridden self.user_ids
        :return: QuerySet for users.models.User model with users from this group
        """
        return users.models.User.objects.filter(id__in=self.user_ids)

    @property
    def user_ids(self):
        """
        :return: QuerySet or list of ids of users which are member of this group
        """
        raise NotImplementedError(
            'Each group should implement user_ids(), but %s doesn\'t' %
            self.__class__.__name__
        )

    @property
    def default_access_type(self):
        if self.list_members_to_everyone:
            return GroupAccess.Type.LIST_MEMBERS
        return GroupAccess.Type.NONE

    def get_access_type_for_user(self, user):
        # Superuser has admin access to any group
        if user.is_superuser:
            return GroupAccess.Type.ADMIN

        user_access = GroupAccessForUser.objects.filter(
            to_group=self, user=user
        ).first()
        if user_access is None:
            user_access = self.default_access_type
        else:
            user_access = user_access.access_type

        # We need to cast queryset to list because following call
        # group_access.group.is_user_in_group() produces another query to database
        # and this query should be finished at this time
        group_accesses = list(GroupAccessForGroup.objects.filter(
            to_group=self
        ).select_related('group').order_by('-access_type'))
        for group_access in group_accesses:
            # Access levels are sorted in decreasing order,
            # so we use the first one granted to the user
            if user_access > group_access.access_type:
                break

            # TODO(artemtab): make proper polymorphic select_related
            if group_access.group.get_real_instance().is_user_in_group(user):
                return group_access.access_type

        return user_access

    def can_user_list_members(self, user):
        return self.get_access_type_for_user(user) >= GroupAccess.Type.LIST_MEMBERS

    def can_user_edit_members(self, user):
        return self.get_access_type_for_user(user) >= GroupAccess.Type.EDIT_MEMBERS

    def is_user_admin(self, user):
        return self.get_access_type_for_user(user) >= GroupAccess.Type.ADMIN


class ManuallyFilledGroup(AbstractGroup):
    # If there will be problems with performance of this method,
    # it can be useful to cache full list of group's members and
    # rebuild it after adding or removing a new member
    @property
    @cache(60)
    def user_ids(self):
        visited_groups_ids = {self.id}
        not_manually_filled_groups_members_ids = set()
        queue = collections.deque([self])
        while queue:
            group = queue.popleft()
            for child_group in group._group_memberships:
                if child_group.member.id not in visited_groups_ids:
                    visited_groups_ids.add(child_group.member.id)
                    if child_group.member.get_real_instance_class() is ManuallyFilledGroup:
                        queue.append(child_group.member.get_real_instance())
                    else:
                        not_manually_filled_groups_members_ids.update(
                            child_group.member.get_real_instance().user_ids
                        )

        return not_manually_filled_groups_members_ids.union(
            UserInGroupMembership.objects.filter(
                group_id__in=visited_groups_ids
            ).values_list('member_id', flat=True).distinct()
        )

    @cached_property
    def _group_memberships(self):
        return (GroupInGroupMembership.objects.filter(group=self)
                .select_related('member'))

    @cached_property
    def _user_memberships(self):
        return (UserInGroupMembership.objects.filter(group=self)
                .select_related('member'))

    @cached_property
    def _memberships(self):
        return self._group_memberships + self._user_memberships

    def add_user(self, user, added_by=None):
        UserInGroupMembership.objects.create(
            group=self,
            member=user,
            added_by=added_by
        )


class GroupMembership(models.Model):
    group = models.ForeignKey(
        ManuallyFilledGroup,
        related_name='+',
        on_delete=models.CASCADE,
    )

    added_by = models.ForeignKey(
        users.models.User,
        null=True,
        blank=True,
        related_name='+',
        on_delete=models.CASCADE,
        help_text='Кем добавлен участник группы. None, если добавлено системой.'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class GroupInGroupMembership(GroupMembership):
    member = models.ForeignKey(
        AbstractGroup,
        related_name='member_in_groups',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return 'Участники %s входят в %s' % (self.member.name, self.group.name)


class UserInGroupMembership(GroupMembership):
    member = models.ForeignKey(
        users.models.User,
        related_name='member_in_groups',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return '%s в %s' % (self.member, self.group.name)


class GroupAccess(polymorphic.models.PolymorphicModel):
    class Type(djchoices.DjangoChoices):
        NONE = djchoices.ChoiceItem(
            value=0,
            label='Нет доступа, группа не видна',
        )
        LIST_MEMBERS = djchoices.ChoiceItem(
            value=10,
            label='Может просматривать участников',
        )
        EDIT_MEMBERS = djchoices.ChoiceItem(
            value=20,
            label='Может добавлять и удалять участников',
        )
        ADMIN = djchoices.ChoiceItem(
            value=30,
            label='Полный доступ',
        )

    to_group = models.ForeignKey(
        AbstractGroup,
        related_name='accesses',
        on_delete=models.CASCADE,
    )

    access_type = models.PositiveIntegerField(
        choices=Type.choices,
        validators=[Type.validator],
        db_index=True,
    )

    created_by = models.ForeignKey(
        users.models.User,
        related_name='+',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Кем выдан доступ. Если None, то системой'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'group access'
        verbose_name_plural = 'group accesses'


class GroupAccessForUser(GroupAccess):
    user = models.ForeignKey(
        users.models.User,
        related_name='+',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return 'Доступ %s к %s' % (self.user.get_full_name(), self.to_group)


class GroupAccessForGroup(GroupAccess):
    group = models.ForeignKey(
        AbstractGroup,
        related_name='+',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return 'Доступ участников %s к %s' % (self.group, self.to_group)


class IntersectionGroup(AbstractGroup):
    groups = models.ManyToManyField(
        AbstractGroup,
        related_name='+',
        help_text='Пересечение каких групп построить'
    )

    @property
    def user_ids(self):
        if self.groups.count() == 0:
            return []

        user_ids = None
        for group in self.groups.all():
            if user_ids is None:
                user_ids = set(group.user_ids)
            else:
                user_ids.intersection_update(group.user_ids)

        return user_ids


class UnionGroup(AbstractGroup):
    groups = models.ManyToManyField(
        AbstractGroup,
        related_name='+',
        help_text='Объединение каких групп построить'
    )

    @property
    def user_ids(self):
        user_ids = set()
        for group in self.groups.all():
            user_ids.update(group.user_ids)

        return user_ids


class DifferenceGroup(AbstractGroup):
    from_group = models.ForeignKey(
        AbstractGroup,
        related_name='+',
        on_delete=models.CASCADE,
        help_text='Участников какой группы взять'
    )

    not_from_group = models.ForeignKey(
        AbstractGroup,
        related_name='+',
        on_delete=models.CASCADE,
        help_text='Участников какой группы вычесть из участников первой группы'
    )

    @property
    def user_ids(self):
        return set(self.from_group.user_ids) - set(self.not_from_group.user_ids)
