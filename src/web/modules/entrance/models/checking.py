from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

import schools.models
import users.models
from . import main as main_models


class CheckingGroup(models.Model):
    school = models.ForeignKey(
        schools.models.School,
        related_name='entrance_checking_groups'
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием'
    )

    name = models.CharField(max_length=100)

    tasks = models.ManyToManyField(
        main_models.FileEntranceExamTask,
        related_name='+'
    )

    def __str__(self):
        return 'Группа проверки %s для %s' % (self.name, self.school)

    class Meta:
        unique_together = ('school', 'short_name')


class UserInCheckingGroup(models.Model):
    user = models.ForeignKey(users.models.User, related_name='+')

    group = models.ForeignKey(CheckingGroup, related_name='users')

    is_actual = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s: пользователь %s' % (self.group, self.user)

    class Meta:
        ordering = ('-created_at', )

    @classmethod
    @transaction.atomic
    def put_user_into_group(cls, user, group):
        for instance in cls.objects.filter(group__school=group.school, user=user):
            instance.is_actual = False
            instance.save()
        cls(user=user, group=group).save()


def get_locked_timeout():
    return timezone.now() + settings.SISTEMA_ENTRANCE_CHECKING_TIMEOUT


class CheckingLock(models.Model):
    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_checking_locks'
    )

    task = models.ForeignKey(
        main_models.EntranceExamTask,
        related_name='+'
    )

    locked_by = models.ForeignKey(
        users.models.User,
        related_name='entrance_checking_locks_by_user'
    )

    locked_until = models.DateTimeField(default=get_locked_timeout)


class CheckedSolution(models.Model):
    solution = models.ForeignKey(
        main_models.EntranceExamTaskSolution,
        related_name='checks'
    )

    score = models.PositiveIntegerField()

    comment = models.TextField(
        help_text='Произвольный комментарий проверяюшего',
        blank=True
    )

    checked_by = models.ForeignKey(users.models.User, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)


class CheckingComment(models.Model):
    school = models.ForeignKey(schools.models.School, related_name='+')

    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_checking_comments'
    )

    comment = models.TextField()

    commented_by = models.ForeignKey(users.models.User, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True)

