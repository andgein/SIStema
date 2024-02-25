import datetime

from django import forms
from allauth.account import forms as account_forms
from allauth.socialaccount import forms as social_account_forms

from django.core import exceptions as django_exceptions
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon, \
    SistemaRadioSelect, SistemaCheckboxSelect

from users import models
from modules.poldnev import forms as poldnev_forms
from users.forms import base as base_forms


def _get_allowed_birth_years():
    year = datetime.date.today().year
    return range(year, year - 60, -1)


def _customize_widgets(form):
    if 'email' in form.fields:
        form.fields['email'].label = 'Эл. почта'
        form.fields['email'].widget = TextInputWithFaIcon(attrs={
            'placeholder': 'Введите почту',
            'class': 'gui-input',
            'fa': 'envelope',
        })
    if 'login' in form.fields:
        form.fields['login'].label = 'Эл. почта'
        form.fields['login'].widget = TextInputWithFaIcon(attrs={
            'placeholder': 'Введите почту',
            'class': 'gui-input',
            'fa': 'user',
        })
    for field_name in ['password', 'password1', 'password2']:
        if field_name in form.fields:
            form.fields[field_name].widget = PasswordInputWithFaIcon(attrs={
                'placeholder': 'Повторите пароль' if field_name == 'password2' else 'Введите пароль',
                'class': 'gui-input',
                'fa': 'lock',
            })


class EmptyIntChoiceField(forms.ChoiceField):
    def __init__(self, choices=(), required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        choices = tuple([(u'', u'')] + list(choices))

        super().__init__(choices=choices, required=required, widget=widget, label=label,
                         initial=initial, help_text=help_text, *args, **kwargs)

    def to_python(self, value):
        if not value:
            return None
        value = super().to_python(value)
        try:
            return int(value)
        except ValueError as e:
            raise django_exceptions.ValidationError(e)


class UserProfileForm(forms.Form):
    poldnev_person = poldnev_forms.PersonField(
        label='Бывали ли вы в ЛКШ?',
        help_text='Оставьте поле пустым, если ещё не были в ЛКШ',
        required=False,
    )

    last_name = forms.CharField(
        required=True,
        label='Фамилия',
        help_text='Как в паспорте или свидетельстве о рождении',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Введите фамилию',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    first_name = forms.CharField(
        required=True,
        label='Имя',
        help_text='Как в паспорте или свидетельстве о рождении',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Введите имя',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    middle_name = forms.CharField(
        required=False,
        label='Отчество',
        help_text='Как в паспорте или свидетельстве о рождении',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Введите отчество',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    sex = forms.TypedChoiceField(
        choices=models.UserProfile.Sex.choices,
        required=True,
        label='Пол',
        widget=SistemaRadioSelect(attrs={'inline': True}),
        coerce=int,
    )

    birth_date = forms.DateField(
        required=True,
        label='Дата рождения',
        widget=forms.DateInput(attrs={
            'class': 'gui-input datetimepicker',
            'data-format': 'DD.MM.YYYY',
            'data-view-mode': 'years',
            'data-pick-time': 'false',
            'placeholder': 'дд.мм.гггг',
        })
    )

    current_class = forms.IntegerField(
        required=True,
        label='Класс',
        help_text=models.UserProfile.get_class_help_text(),
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'gui-input'
        })
    )

    region = forms.CharField(
        required=True,
        label='Субъект РФ',
        help_text='или страна, если не Россия',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'building-o',
            'placeholder': 'Например, Москва или Тюменская область'
        })
    )

    city = forms.CharField(
        required=True,
        label='Населённый пункт',
        help_text='в котором находится школа',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Город, деревня, село..',
            'class': 'gui-input',
            'fa': 'building-o',
        })
    )

    school_name = forms.CharField(
        required=True,
        label='Школа',
        help_text='Например, «Лицей №88»',
        max_length=250,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'graduation-cap',
        })
    )

    phone = forms.CharField(
        required=True,
        label='Мобильный телефон',
        help_text='Позвоним в экстренной ситуации. Например, +7 900 000 00 00',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': '+7 900 000 00 00',
            'class': 'gui-input',
            'fa': 'phone',
        })
    )

    vk = forms.CharField(
        required=True,
        label='Адрес страницы ВКонтакте',
        max_length=100,
        help_text='Адрес страницы ВКонтакте нужен нам для оперативной '
                  'и удобной связи с вами. '
                  'Если у вас нет страницы, заполните поле прочерком',
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'vk.com/example',
            'class': 'gui-input',
            'fa': 'vk',
        })
    )

    telegram = forms.CharField(
        required=False,
        label='Ник в Телеграме',
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': '@nick',
            'class': 'gui-input',
            'fa': 'paper-plane',
        })
    )

    codeforces_handle = forms.CharField(
        required=False,
        label=mark_safe('Хэндл на&nbsp;<a href="https://codeforces.com">codeforces.com</a>'),
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': '',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    informatics_username = forms.CharField(
        required=False,
        label=mark_safe('Имя пользователя на&nbsp;<a href="http://informatics.msk.ru">informatics.msk.ru</a>'),
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'placeholder': '',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    citizenship = EmptyIntChoiceField(
        models.UserProfile.Citizenship.choices,
        label='Гражданство',
        help_text='Выберите «Другое», если имеете несколько гражданств',
        required=False,
    )
    citizenship_other = forms.CharField(
        label='Другое гражданство',
        # TODO hide this field, if citizenship != Citizenship.OTHER
        help_text='Если вы указали «Другое», укажите здесь своё гражданство (или несколько через запятую)',
        required=False,
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'file-text-o',
        })
    )

    document_type = EmptyIntChoiceField(
        models.UserProfile.DocumentType.choices,
        label='Документ, удостоверяющий личность',
        required=False,
    )
    document_number = forms.CharField(
        label='Номер документа',
        help_text='Укажите и серию, и номер документа',
        required=False,
        max_length=100,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'file-text-o',
        })
    )

    t_shirt_size = forms.TypedChoiceField(
        choices=models.UserProfile.TShirtSize.choices,
        required=False,
        label='Размер футболки',
        widget=SistemaRadioSelect(attrs={'inline': True}),
        coerce=int,
        empty_value=None,
    )

    def __init__(self, *args, all_fields_are_required=False, **kwargs):
        if 'initial' in kwargs and 'has_accepted_terms' in kwargs['initial']:
            # As has_accepted_terms is a ChoiceField,
            # its value should be a list, not a bool
            kwargs['initial']['has_accepted_terms'] = \
                [kwargs['initial']['has_accepted_terms']]
        super().__init__(*args, **kwargs)
        if all_fields_are_required:
            for field_name in models.UserProfile.get_fully_filled_field_names():
                self.fields[field_name].required = True

    def fill_user_profile(self, user):
        if not user.is_authenticated:
            user_profile = models.UserProfile()
        elif hasattr(user, 'profile'):
            user_profile = user.profile
        else:
            user_profile = models.UserProfile(user=user)
        for field_name in user_profile.get_field_names():
            if field_name in self.cleaned_data:
                field_value = self.cleaned_data.get(field_name)
                # has_accepted_terms is a BooleanField in the database, so we need to
                # transform list to bool
                if field_name == 'has_accepted_terms':
                    field_value = field_value[0]
                setattr(user_profile, field_name, field_value)
        return user_profile


class SignupForm(account_forms.SignupForm, UserProfileForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.SIGNUP
        super().__init__(*args, **kwargs)
        _customize_widgets(self)

        exceptions_list = ['middle_name', 'poldnev_person']
        field_names_to_drop = [field_name
                               for field_name, field in self.fields.items()
                               if not field.required and field_name not in exceptions_list]
        for field_name in field_names_to_drop:
            self.fields.pop(field_name)


class SocialSignupForm(social_account_forms.SignupForm, UserProfileForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.SIGNUP
        super().__init__(*args, **kwargs)
        self.fields['password1'] = account_forms.PasswordField(label=_("Password"))
        self.fields['password2'] = account_forms.PasswordField(label=_("Password (again)"))
        _customize_widgets(self)


class LoginForm(account_forms.LoginForm, base_forms.AccountBaseForm):
    error_messages = {
        'account_inactive':
            'Ваш аккаунт выключен. Если это произошло по ошибке, напишите нам на lksh@lksh.ru',

        'email_password_mismatch':
            'Эл. почта или пароль неверны. Попробуйте ещё раз',

        'username_password_mismatch':
            'Логин или пароль неверны. Попробуйте ещё раз',

        'username_email_password_mismatch':
            'Логин или пароль неверны. Попробуйте ещё раз',
    }

    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.LOGIN
        super().__init__(*args, **kwargs)
        _customize_widgets(self)


class ResetPasswordForm(account_forms.ResetPasswordForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.NONE
        super().__init__(*args, **kwargs)
        _customize_widgets(self)


class ChangePasswordForm(account_forms.ChangePasswordForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.HIDE
        super().__init__(*args, **kwargs)
        _customize_widgets(self)


class ResetPasswordKeyForm(account_forms.ResetPasswordKeyForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.NONE
        super().__init__(*args, **kwargs)
        _customize_widgets(self)
