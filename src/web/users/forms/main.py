import datetime

from django import forms
from allauth.account import forms as account_forms
from allauth.socialaccount import forms as social_account_forms

from django.utils.translation import ugettext_lazy as _
from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon

from users import models
from users.forms import base as base_forms


def _get_allowed_birth_years():
    year = datetime.date.today().year
    return range(year, year - 60, -1)


def _customize_widgets(form):
    if 'email' in form.fields:
        form.fields['email'].widget = TextInputWithFaIcon(attrs={
            'placeholder': 'Введите почту',
            'class': 'gui-input',
            'fa': 'envelope',
        })
    if 'login' in form.fields:
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


class LoginForm(account_forms.LoginForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.LOGIN
        super(LoginForm, self).__init__(*args, **kwargs)
        _customize_widgets(self)


class UserProfileForm(forms.Form):
    last_name = forms.CharField(required=True,
                                label='Фамилия',
                                widget=TextInputWithFaIcon(attrs={
                                    'placeholder': 'Введите фамилию',
                                    'class': 'gui-input',
                                    'autofocus': 'autofocus',
                                    'fa': 'user',
                                }))

    first_name = forms.CharField(required=True,
                                 label='Имя',
                                 widget=TextInputWithFaIcon(attrs={
                                     'placeholder': 'Введите имя',
                                     'class': 'gui-input',
                                     'fa': 'user',
                                 }))

    middle_name = forms.CharField(required=True,
                                  label='Имя',
                                  widget=TextInputWithFaIcon(attrs={
                                      'placeholder': 'Введите отчество (если есть)',
                                      'class': 'gui-input',
                                      'fa': 'user',
                                  }))

    sex = forms.ChoiceField(models.UserProfile.Sex.choices,
                            required=True,
                            label='Пол',
                            widget=forms.RadioSelect)

    birth_date = forms.DateField(required=True,
                                 label='Дата рождения',
                                 widget=forms.DateInput(format='%d.%m.%Y')
                                 )  # TODO widget=forms.SelectDateWidget(years=_get_allowed_birth_years()))

    current_class = forms.IntegerField(label='Класс',
                                       min_value=1,
                                       required=False)

    region = forms.CharField(required=True,
                             label='Субъект РФ',
                             help_text='или страна, если не Россия')
    city = forms.CharField(required=True,
                           label='Населённый пункт')
    school_name = forms.CharField(label='Школа',
                                  required=False)

    phone = forms.CharField(required=True,
                            label='Телефон',
                            widget=TextInputWithFaIcon(attrs={
                                'placeholder': '+7(901)234-56-78',
                                'class': 'gui-input',
                                'fa': 'phone',
                            }))

    nationality = forms.CharField(label='Национальность',
                                  required=False)

    document_type = forms.ChoiceField(models.UserProfile.DocumentType.choices,
                                      label='Тип документа',
                                      required=False)
    document_number = forms.CharField(label='Номер документа',
                                      required=False)

    insurance_number = forms.CharField(label='Номер медицинского полиса',
                                       required=False)


class SignupForm(account_forms.SignupForm, UserProfileForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.SIGNUP
        super(SignupForm, self).__init__(*args, **kwargs)
        _customize_widgets(self)


class SocialSignupForm(social_account_forms.SignupForm, UserProfileForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.SIGNUP
        super(SocialSignupForm, self).__init__(*args, **kwargs)
        self.fields['password1'] = account_forms.PasswordField(label=_("Password"))
        self.fields['password2'] = account_forms.PasswordField(label=_("Password (again)"))
        _customize_widgets(self)


class ResetPasswordForm(account_forms.ResetPasswordForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.NONE
        super(ResetPasswordForm, self).__init__(*args, **kwargs)
        _customize_widgets(self)


class ResetPasswordKeyForm(account_forms.ResetPasswordKeyForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.NONE
        super(ResetPasswordKeyForm, self).__init__(*args, **kwargs)
        _customize_widgets(self)
