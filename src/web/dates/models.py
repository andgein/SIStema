from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class KeyDate(models.Model):
    """
    Represents any key date in SIStema. Supports exceptions for specific users.
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

    def __str__(self):
        return '{}: {}'.format(self.datetime, self.name)

    def datetime_for_user(self, user):
        """
        Datetime for the specific user, considering exceptions.
        """
        exception = self.exceptions.filter(user=user).first()
        if exception is not None:
            return exception.datetime

        return self.datetime

    def passed_for_user(self, user):
        """
        True if the date is in the past for user, taking exceptions into account
        """
        return self.datetime_for_user(user) < timezone.now()


class KeyDateException(models.Model):
    """
    Key date exceptions for an individual user
    """

    key_date = models.ForeignKey(
        'KeyDate',
        on_delete=models.CASCADE,
        related_name='exceptions',
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
        verbose_name = _('key date exception')
        verbose_name_plural = _('key date exceptions')
        unique_together = ('key_date', 'user')

    def __str__(self):
        return 'Перенос даты "{}" для {} на {}'.format(
            self.key_date, self.user, self.datetime)
