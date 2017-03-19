import datetime

from django import forms
from allauth.account import forms as account_forms
from allauth.socialaccount import forms as social_account_forms

from django.utils.translation import ugettext_lazy as _
from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon,\
    SistemaRadioSelect

from users import models
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


class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, choices=(), required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        choices = tuple([(u'', u'')] + list(choices))

        super().__init__(choices=choices, required=required, widget=widget, label=label,
                         initial=initial, help_text=help_text, *args, **kwargs)

    def to_python(self, value):
        if value == '' or value is None:
            return None
        return super().to_python(value)


class UserProfileForm(forms.Form):
    last_name = forms.CharField(
        required=True,
        label='Фамилия',
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Введите фамилию',
            'class': 'gui-input',
            'autofocus': 'autofocus',
            'fa': 'user',
        })
    )

    first_name = forms.CharField(
        required=True,
        label='Имя',
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Введите имя',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    middle_name = forms.CharField(
        required=True,
        label='Отчество',
        widget=TextInputWithFaIcon(attrs={
            'placeholder': 'Введите отчество',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    sex = forms.ChoiceField(
        models.UserProfile.Sex.choices,
        required=True,
        label='Пол',
        widget=SistemaRadioSelect(attrs={'inline': True})
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
    )  # TODO widget=forms.SelectDateWidget(years=_get_allowed_birth_years()))

    current_class = forms.IntegerField(
        required=True,
        label='Класс',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'gui-input'
        })
    )

    region = forms.CharField(
        required=True,
        label='Субъект РФ',
        help_text='или страна, если не Россия',
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
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'graduation-cap',
        })
    )

    phone = forms.CharField(
        required=True,
        label='Телефон',
        help_text='С кодом города',
        widget=TextInputWithFaIcon(attrs={
            'placeholder': '+7 900 000-00-00',
            'class': 'gui-input',
            'fa': 'phone',
        })
    )

    citizenship = EmptyChoiceField(
        models.UserProfile.Citizenship.choices,
        label='Гражданство',
        help_text='Выберите «Другое», если имеете несколько гражданств',
        required=False
    )
    citizenship_other = forms.CharField(
        label='Другое гражданство',
        #TODO hide this field, if citizenship != Citizenship.OTHER
        help_text='Если вы указали «Другое», укажите здесь своё гражданство (или несколько через запятую)',
        required=False,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'file-text-o',
        })
    )

    document_type = EmptyChoiceField(
        models.UserProfile.DocumentType.choices,
        label='Документ, удостоверяющий личность',
        required=False
    )
    document_number = forms.CharField(
        label='Номер документа',
        help_text='Укажите и серию, и номер документа',
        required=False,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'file-text-o',
        })
    )

    insurance_number = forms.CharField(
        label='Номер медицинского полиса',
        help_text='Только для проживающих в России',
        required=False,
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'file-text-o',
        })
    )


class SignupForm(account_forms.SignupForm, UserProfileForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.SIGNUP
        super().__init__(*args, **kwargs)
        _customize_widgets(self)


class SocialSignupForm(social_account_forms.SignupForm, UserProfileForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.SIGNUP
        super().__init__(*args, **kwargs)
        self.fields['password1'] = account_forms.PasswordField(label=_("Password"))
        self.fields['password2'] = account_forms.PasswordField(label=_("Password (again)"))
        _customize_widgets(self)


class LoginForm(account_forms.LoginForm, base_forms.AccountBaseForm):
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
