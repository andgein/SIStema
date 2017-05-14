from constance import config
from django.db import models, transaction
from django.utils import timezone

import schools.models
import users.models
from . import main as main_models


class CheckingGroup(models.Model):
    school = models.ForeignKey(
        schools.models.School,
        related_name='entrance_checking_groups',
        on_delete=models.CASCADE,
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. Лучше обойтись латинскими буквами, '
                  'цифрами и подчёркиванием',
    )

    name = models.CharField(max_length=100)

    tasks = models.ManyToManyField(
        main_models.FileEntranceExamTask,
        related_name='+',
        blank=True
    )

    def __str__(self):
        return 'Группа проверки %s для %s' % (self.name, self.school)

    @property
    def actual_users(self):
        return self.all_time_users.filter(is_actual=True)

    class Meta:
        unique_together = ('school', 'short_name')


class UserInCheckingGroup(models.Model):
    user = models.ForeignKey(
        users.models.User,
        related_name='+',
        on_delete=models.CASCADE,
    )

    group = models.ForeignKey(
        CheckingGroup,
        related_name='all_time_users',
        on_delete=models.CASCADE,
    )

    is_actual = models.BooleanField(
        default=True,
        help_text='True для актуальных записей, False для исторических'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    def __str__(self):
        return '%s: пользователь %s' % (self.group, self.user)

    @classmethod
    @transaction.atomic
    def move_user_into_group(cls, user, group):
        (cls.objects
         .filter(group__school=group.school, user=user)
         .update(is_actual=False)
         )
        cls.objects.create(user=user, group=group)


def get_locked_timeout():
    return (timezone.now() +
            timezone.timedelta(minutes=config.SISTEMA_ENTRANCE_CHECKING_TIMEOUT))


class CheckingLock(models.Model):
    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_checking_locks',
        on_delete=models.CASCADE,
    )

    task = models.ForeignKey(
        main_models.EntranceExamTask,
        related_name='+',
        on_delete=models.CASCADE,
    )

    locked_by = models.ForeignKey(
        users.models.User,
        related_name='entrance_checking_locks_by_user',
        on_delete=models.CASCADE,
    )

    locked_until = models.DateTimeField(
        default=get_locked_timeout,
        db_index=True
    )


class CheckedSolution(models.Model):
    solution = models.ForeignKey(
        main_models.EntranceExamTaskSolution,
        related_name='checks',
        on_delete=models.CASCADE,
    )

    score = models.PositiveIntegerField()

    comment = models.TextField(
        help_text='Произвольный комментарий проверяюшего',
        blank=True
    )

    checked_by = models.ForeignKey(
        users.models.User,
        related_name='+',
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )


class CheckingComment(models.Model):
    school = models.ForeignKey(
        schools.models.School,
        related_name='+',
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        users.models.User,
        related_name='entrance_checking_comments',
        on_delete=models.CASCADE,
    )

    comment = models.TextField()

    commented_by = models.ForeignKey(
        users.models.User,
        related_name='+',
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
