import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class KeyDate(models.Model):
    """
    Represents any key date in SIStema.

    Supports exceptions for specific users and groups:
    - If user has a personal exception, then it will be used. All the group
      exceptions are ignored.
    - If user is a member of several groups each having an exception, then the
      latest one will be used.
    """

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='key_dates',
        null=True,
        blank=True,
        help_text="Школа, к которой относится эта дата. Поле может быть "
                  "пустым, если дата не относится ни к какой школе.",
    )

    short_name = models.SlugField(
        help_text="Может состоять только из букв, цифр, знака подчеркивания и "
                  "дефиса.")

    datetime = models.DateTimeField(
        verbose_name='дата и время',
    )

    name = models.CharField(
        blank=True,
        max_length=120,
        verbose_name='название',
        help_text='Нужно, чтобы быстро понимать, к чему относится дата',
    )

    class Meta:
        verbose_name = _('key date')
        verbose_name_plural = _('key dates')
        unique_together = ('school', 'short_name')

    def __str__(self):
        return '{}: {}'.format(self.datetime, self.name)

    def datetime_for_user(self, user):
        """
        Datetime for the specific user, considering exceptions.
        """
        user_exception = self.user_exceptions.filter(user=user).first()
        if user_exception is not None:
            return user_exception.datetime

        latest_datetime = None
        for group_exception in self.group_exceptions.all():
            if group_exception.group.is_user_in_group(user):
                if (latest_datetime is None or
                        latest_datetime < group_exception.datetime):
                    latest_datetime = group_exception.datetime
        if latest_datetime is not None:
            return latest_datetime

        return self.datetime

    def passed_for_user(self, user):
        """
        True if the date is in the past for user, taking exceptions into account
        """
        return self.datetime_for_user(user) < timezone.now()

    # A unique object used as the default argument value in the clone method.
    # Needed, because we want to handle None.
    KEEP_VALUE = object()

    def clone(self,
              *,
              school=KEEP_VALUE,
              short_name=KEEP_VALUE,
              name=KEEP_VALUE,
              datetime=KEEP_VALUE,
              copy_exceptions=False):
        """
        Make and return the full copy of the key date. The copy should have
        a unique `(school, short_name)` combination. You can change either of
        them by setting the corresponding method arguments.

        :param school: The school for the new key date. By default is equal to
            the source key date's school.
        :param short_name: The short name for the new key date. By default is
            equal to the source key date's short name.
        :param name: The name for the new key date. By default is equal to the
            source key date's name.
        :param datetime: The datetime for the new key date. By default is equal
            to the source key date's datetime.
        :param copy_exceptions: If true exceptions will be copied to the new key
            date.
        :return: The fresh copy of the key date.
        """
        if self.pk is None:
            raise ValueError(
                "The key date should be in database to be cloned")

        if school is self.KEEP_VALUE:
            school = self.school
        if short_name is self.KEEP_VALUE:
            short_name = self.short_name
        if name == self.KEEP_VALUE:
            name = self.name
        if datetime == self.KEEP_VALUE:
            datetime = self.datetime

        new_key_date = self.__class__.objects.create(
            school=school,
            short_name=short_name,
            name=name,
            datetime=datetime,
        )

        if copy_exceptions:
            for exception in self.user_exceptions.all():
                exception.pk = None
                exception.key_date = new_key_date
                exception.save()

        return new_key_date


class UserKeyDateException(models.Model):
    """
    Exception for a key date for a specific user. Only single exception is
    allowed per user for a given date.
    """

    key_date = models.ForeignKey(
        'KeyDate',
        on_delete=models.CASCADE,
        related_name='user_exceptions',
    )

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='key_date_exceptions',
        help_text='Пользователь, для которого будет применено исключение',
    )

    datetime = models.DateTimeField(
        verbose_name='Новое время',
    )

    class Meta:
        verbose_name = _('key date exception for user')
        verbose_name_plural = _('key date exceptions for users')
        unique_together = ('key_date', 'user')

    def __str__(self):
        return 'Перенос даты "{}" для {} на {}'.format(
            self.key_date, self.user, self.datetime)


class GroupKeyDateException(models.Model):
    """
    Exception for a key date for a specific user. Only single exception is
    allowed per group for a given date.

    If user belongs to several groups and each of them has an exception, the
    latest one will be used.
    """

    key_date = models.ForeignKey(
        'KeyDate',
        on_delete=models.CASCADE,
        related_name='group_exceptions',
    )

    group = models.ForeignKey(
        'groups.AbstractGroup',
        on_delete=models.CASCADE,
        related_name='key_date_exceptions',
        help_text='Группа, для членов которой будет применено исключение',
    )

    datetime = models.DateTimeField(
        verbose_name='Новое время',
    )

    class Meta:
        verbose_name = _(' key date exception for group')
        verbose_name_plural = _('key date exceptions for groups')
        unique_together = ('key_date', 'group')

    def __str__(self):
        return 'Перенос даты "{}" для {} на {}'.format(
            self.key_date, self.group, self.datetime)
