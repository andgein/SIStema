import datetime

from django.db import models
from djchoices import choices
import django.db.transaction


__all__ = ['UserProfile']


class UserProfile(models.Model):
    class Sex(choices.DjangoChoices):
        FEMALE = choices.ChoiceItem(1, 'женский')
        MALE = choices.ChoiceItem(2, 'мужской')

    class DocumentType(choices.DjangoChoices):
        RUSSIAN_PASSPORT = choices.ChoiceItem(1, 'Российский паспорт')
        BIRTH_CERTIFICATE = choices.ChoiceItem(2, 'Свидетельство о рождении')
        ALIEN_PASSPORT = choices.ChoiceItem(3, 'Заграничный паспорт')
        ANOTHER_COUNTRY_PASSPORT = choices.ChoiceItem(
            4, 'Паспорт другого государства')
        OTHER_DOCUMENT = choices.ChoiceItem(-1, 'Другой')

    class Citizenship(choices.DjangoChoices):
        RUSSIA = choices.ChoiceItem(1, 'Россия')
        KAZAKHSTAN = choices.ChoiceItem(2, 'Казахстан')
        BELARUS = choices.ChoiceItem(3, 'Беларусь')
        TAJIKISTAN = choices.ChoiceItem(4, 'Таджикистан')
        OTHER = choices.ChoiceItem(-1, 'Другое')

    class TShirtSize(choices.DjangoChoices):
        XS = choices.ChoiceItem(1, 'XS')
        S = choices.ChoiceItem(2, 'S')
        M = choices.ChoiceItem(3, 'M')
        L = choices.ChoiceItem(4, 'L')
        XL = choices.ChoiceItem(5, 'XL')
        XXL = choices.ChoiceItem(6, 'XXL')

    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='profile',
    )

    updated_at = models.DateTimeField(auto_now=True)

    first_name = models.CharField('Имя', max_length=100, blank=True, default='')
    middle_name = models.CharField(
        'Отчество',
        max_length=100,
        blank=True,
        default='',
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=100,
        blank=True,
        default='',
    )

    sex = models.PositiveIntegerField(
        'Пол',
        choices=Sex.choices,
        validators=[Sex.validator],
        null=True,
        blank=True,
    )
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    _zero_class_year = models.PositiveIntegerField(
        'Год поступления в "нулевой" класс',
        null=True,
        blank=True,
        help_text='используется для вычисления текущего класса',
        db_column='zero_class_year',
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

    school_name = models.CharField(
        'Школа',
        max_length=250,
        blank=True,
        default='',
    )

    phone = models.CharField('Телефон', max_length=100, blank=True, default='')
    vk = models.CharField('ВКонтакте', max_length=100, blank=True, default='')
    telegram = models.CharField(
        'Телеграм',
        max_length=100,
        blank=True,
        default='',
    )

    # TODO(artemtab): find a way to remove dependency on the non-core module
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

    citizenship_other = models.CharField(
        'Другое гражданство',
        blank=True,
        max_length=100,
        default='',
    )

    document_type = models.IntegerField(
        'Тип документа',
        null=True,
        blank=True,
        choices=DocumentType.choices,
        validators=[DocumentType.validator],
    )
    document_number = models.CharField(
        'Номер документа',
        max_length=100,
        blank=True,
        default='',
    )

    t_shirt_size = models.IntegerField(
        verbose_name='Размер футболки',
        null=True,
        blank=True,
        choices=TShirtSize.choices,
        validators=[TShirtSize.validator],
    )

    has_accepted_terms = models.BooleanField(
        'Согласие на обработку персональных данных',
        default=False,
    )

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
        return ('Класс в %d–%d учебном году. Если вы обучаетесь не в РФ, '
                'введите максимально подходящий класс по Российской системе'
                % (year, year + 1))

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
            't_shirt_size',
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
