from django.db import models
from django.utils.translation import gettext_lazy as _


__all__ = ['UserList']


class UserList(models.Model):
    """
    A generic list of users. Provides a single point for making and maintaining
    such list. Some examples:
    - Users who should fill a questionnaire
    - Users who allowed to apply to school
    """
    name = models.CharField(
        max_length=120,
        verbose_name='Название',
        help_text='Чтобы быстро понимать, для чего этот список предназначен',
    )

    users = models.ManyToManyField(
        'User',
        related_name='+',
        verbose_name=_('users'),
    )

    class Meta:
        verbose_name = _('user list')
        verbose_name_plural = _('user lists')

    def __str__(self):
        return 'Список пользователей "{}"'.format(self.name)

    def contains_user(self, user):
        return self.users.filter(id=user.id).exists()
