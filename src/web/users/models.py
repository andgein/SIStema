from django.contrib.auth import models as auth_models
from django.core import mail, validators
from django.db import models
from django.utils import crypto
from django.utils.translation import ugettext_lazy as _

def generate_random_secret_string():
    return crypto.get_random_string(length=32)


class UserManager(auth_models.UserManager):
    pass


# See the django.contrib.auth.models.User for details
# We need to copy it here for enlarge username, first_name and last_name's
# lengths from 30 to 100 characters
class User(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    username = models.CharField(
        _('username'),
        max_length=100,
        unique=True,
        help_text=_('Required. 100 characters or fewer. Letters, digits and '
                    '@/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(
                r'^[\w\d.@+-]+$',
                _('Enter a valid username. This value may contain only '
                  'letters, numbers ' 'and @/./+/-/_ characters.')
            ),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)

    # Sistema custom fields
    mail_confirmation_token = models.CharField(
        default=generate_random_secret_string, max_length=32)

    is_email_confirmed = models.BooleanField(default=True)
    # End of Sistema custom fields

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Sends an email to this User."""
        mail.send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return '%s %s (%s)' % (self.last_name, self.first_name, self.email)


class UserPasswordRecovery(models.Model):
    user = models.ForeignKey(User)

    recovery_token = models.CharField(default=generate_random_secret_string,
                                      max_length=32)

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
