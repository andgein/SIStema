import datetime

from django.contrib.auth import models as auth_models
from django.core import mail, validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djchoices import choices
import django.db.transaction


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

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between.
        """
        if hasattr(self, 'profile'):
            full_name = '%s %s' % (self.profile.first_name,
                                   self.profile.last_name)
        else:
            full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        if hasattr(self, 'profile'):
            return self.profile.first_name
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Sends an email to this User."""
        mail.send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return '%d %s (%s)' % (self.id, self.get_full_name(), self.email)


class UserProfile(models.Model):
    class Sex(choices.DjangoChoices):
        FEMALE = choices.ChoiceItem(1, 'женский')
        MALE = choices.ChoiceItem(2, 'мужской')

    class DocumentType(choices.DjangoChoices):
        RUSSIAN_PASSPORT = choices.ChoiceItem(1, 'Российский паспорт')
        BIRTH_CERTIFICATE = choices.ChoiceItem(2, 'Свидетельство о рождении')
        ALIEN_PASSPORT = choices.ChoiceItem(3, 'Заграничный паспорт')
        ANOTHER_COUNTRY_PASSPORT = choices.ChoiceItem(4, 'Паспорт другого государства')
        OTHER_DOCUMENT = choices.ChoiceItem(-1, 'Другой')

    class Citizenship(choices.DjangoChoices):
        RUSSIA = choices.ChoiceItem(1, 'Россия')
        KAZAKHSTAN = choices.ChoiceItem(2, 'Казахстан')
        BELARUS = choices.ChoiceItem(3, 'Беларусь')
        TAJIKISTAN = choices.ChoiceItem(4, 'Таджикистан')
        OTHER = choices.ChoiceItem(-1, 'Другое')

    user = models.OneToOneField(User, related_name='profile')
    updated_at = models.DateTimeField(auto_now=True)

    first_name = models.CharField('Имя', max_length=100, blank=True, default='')
    middle_name = models.CharField('Отчество', max_length=100, blank=True, default='')
    last_name = models.CharField('Фамилия', max_length=100, blank=True, default='')

    sex = models.PositiveIntegerField(
        'Пол',
        choices=Sex.choices,
        validators=[Sex.validator],
        null=True,
        blank=True,
    )
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    _zero_class_year = models.PositiveIntegerField('Год поступления в "нулевой" класс',
                                                   null=True,
                                                   help_text='используется для вычисления текущего класса',
                                                   db_column='zero_class_year',
                                                   blank=True,
                                                   )

    region = models.CharField(
        'Субъект РФ',
        max_length=100,
        blank=True,
        default='',
        help_text='или страна, если не Россия'
    )
    city = models.CharField(
        'Населённый пункт',
        max_length=100,
        blank=True,
        default='',
        help_text='в котором находится школа'
    )

    school_name = models.CharField('Школа', max_length=250, blank=True, default='')

    phone = models.CharField('Телефон', max_length=100, blank=True, default='')
    vk = models.CharField('ВКонтакте', max_length=100, blank=True, default='')
    telegram = models.CharField('Телеграм', max_length=100, blank=True, default='')

    poldnev_person = models.ForeignKey(
        'poldnev.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profiles',
    )

    citizenship = models.IntegerField(
        'Гражданство',
        choices=Citizenship.choices,
        validators=[Citizenship.validator],
        null=True,
        blank=True,
    )

    citizenship_other = models.CharField('Другое гражданство', max_length=100, blank=True, default='')

    document_type = models.IntegerField(
        'Тип документа',
        choices=DocumentType.choices,
        validators=[DocumentType.validator],
        null=True,
        blank=True,
    )
    document_number = models.CharField('Номер документа', max_length=100, blank=True, default='')

    has_accepted_terms = models.BooleanField('Согласие на обработку персональных данных', default=False)

    def save(self):
        self.user.first_name = self.first_name
        self.user.last_name = self.last_name
        with django.db.transaction.atomic():
            self.user.save()
            super().save()

    def get_zero_class_year(self):
        return self._zero_class_year

    @classmethod
    def get_class_help_text(cls, date=None):
        if not date:
            date = datetime.date.today()
        year = date.year
        if date.month < 9:
            year -= 1
        return ('Класс в %d–%d учебном году. Если вы обучаетесь не в РФ, введите '
                'максимально подходящий класс по Российской системе' % (year, year + 1))

    def get_class(self, date=None):
        if self._zero_class_year is None:
            return None
        if not date:
            date = datetime.date.today()
        result = date.year - self._zero_class_year
        if date.month < 9:
            result -= 1
        return result

    def set_class(self, value, date=None):
        if value is None:
            self._zero_class_year = None
            return
        if not date:
            date = datetime.date.today()
        self._zero_class_year = date.year - value
        if date.month < 9:
            self._zero_class_year -= 1

    current_class = property(get_class, set_class)

    @classmethod
    def get_field_names(cls):
        return [
            'first_name',
            'middle_name',
            'last_name',
            'sex',
            'birth_date',
            'poldnev_person',
            'current_class',
            'region',
            'city',
            'school_name',
            'phone',
            'vk',
            'telegram',
            'citizenship',
            'citizenship_other',
            'document_type',
            'document_number',
            'has_accepted_terms',
        ]

    @classmethod
    def get_fully_filled_field_names(cls):
        """
        Returns list of field names which should be filled
        in the fully-filled profile
        """
        fields = cls.get_field_names()
        fields.remove('middle_name')
        fields.remove('citizenship_other')
        fields.remove('poldnev_person')
        fields.remove('telegram')
        return fields

    def is_fully_filled(self):
        for field_name in self.get_fully_filled_field_names():
            field = getattr(self, field_name)
            if field is None or field == '':
                return False
        return True
