import datetime

from django import forms
from allauth.account import forms as account_forms
from allauth.socialaccount import forms as social_account_forms

from django.core import exceptions as django_exceptions
from django.utils.translation import ugettext_lazy as _
from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon

from users import models
from modules.poldnev import forms as poldnev_forms
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
        help_text='Оставьте поле пустым, если ещё не были в ЛКШ'
    )

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
            'placeholder': 'Введите отчество (если есть)',
            'class': 'gui-input',
            'fa': 'user',
        })
    )

    sex = forms.TypedChoiceField(
        models.UserProfile.Sex.choices,
        required=True,
        label='Пол',
        widget=forms.RadioSelect,
        coerce=int,
    )

    birth_date = forms.DateField(
        required=True,
        label='Дата рождения',
        widget=forms.DateInput(format='%d.%m.%Y')
    )  # TODO widget=forms.SelectDateWidget(years=_get_allowed_birth_years()))

    current_class = forms.IntegerField(
        required=True,
        label='Класс',
        min_value=1,
    )

    region = forms.CharField(
        required=True,
        label='Субъект РФ',
        help_text='или страна, если не Россия',
        widget=TextInputWithFaIcon(attrs={
            'class': 'gui-input',
            'fa': 'building-o',
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
            'placeholder': '+7(901)234-56-78',
            'class': 'gui-input',
            'fa': 'phone',
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
        #TODO hide this field, if citizenship != Citizenship.OTHER
        help_text='Если вы указали «Другое», укажите здесь своё гражданство (или несколько через запятую)',
        required=False,
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

    def fill_user_profile(self, request):
        if request.user_profile:
            user_profile = request.user_profile
        elif request.user.is_authenticated:
            user_profile = models.UserProfile(user=request.user)
        else:
            user_profile = models.UserProfile()
        for field_name in user_profile.get_field_names():
            setattr(user_profile, field_name, self.cleaned_data.get(field_name))
        return user_profile


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


class ResetPasswordKeyForm(account_forms.ResetPasswordKeyForm, base_forms.AccountBaseForm):
    def __init__(self, *args, **kwargs):
        kwargs['active_tab'] = base_forms.AccountBaseForm.Tab.NONE
        super().__init__(*args, **kwargs)
        _customize_widgets(self)
