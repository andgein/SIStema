from constance import config
from django.db import models, IntegrityError
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

    group = models.ForeignKey(
        'groups.AbstractGroup',
        on_delete=models.CASCADE,
        related_name='+',
    )

    def __str__(self):
        return 'Группа проверки %s для %s' % (self.name, self.school)

    class Meta:
        unique_together = ('school', 'short_name')

    def save(self, *args, **kwargs):
        if self.school_id != self.group.school_id:
            raise IntegrityError(
                "Checking group should belong to the same school such as group")
        super().save(*args, **kwargs)


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
