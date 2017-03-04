from django import forms
from allauth.account import forms as account_forms
from allauth.account import adapter as account_adapter
from allauth.account import utils as account_utils

from django.utils.translation import ugettext_lazy as _
from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon

from users import models

import datetime


def _get_allowed_birth_years():
    year = datetime.date.today().year
    return range(year, year - 60, -1)


class CenteredForm(forms.Form):
    class Meta:
        show_fields = ()


class SignupForm(CenteredForm):
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

    def __init__(self, **kwargs):
        super(SignupForm, self).__init__(**kwargs)
        if hasattr(self, 'sociallogin'):
            self.fields['password1'] = account_forms.PasswordField(label=_("Password"))
            self.fields['password2'] = account_forms.PasswordField(label=_("Password (again)"))

    def clean(self):
        super(SignupForm, self).clean()
        if hasattr(self, 'sociallogin'):
            password1 = self.cleaned_data.get('password1')
            password2 = self.cleaned_data.get('password2')
            if password1 and password2 and password1 != password2:
                self.add_error('password2', self.error_class(["You must type the same password each time."]))
            if password1:
                dummy_user = account_utils.get_user_model()
                try:
                    account_adapter.get_adapter().clean_password(
                        password1,
                        user=dummy_user)
                except forms.ValidationError as e:
                    self.add_error('password1', e)

    def signup(self, request, user):  # TODO check can delete 'request'
        if hasattr(self, 'sociallogin'):
            user.set_password(self.cleaned_data.get('password1'))
        user.first_name = self.cleaned_data.get('first_name')
        user.second_name = self.cleaned_data.get('second_name')
        user.save()
        profile = models.UserProfile(user=user,
                                     first_name=self.cleaned_data.get('first_name'),
                                     middle_name=self.cleaned_data.get('middle_name'),
                                     last_name=self.cleaned_data.get('last_name'),
                                     sex=self.cleaned_data.get('sex'),
                                     birth_date=self.cleaned_data.get('birth_date'),
                                     region=self.cleaned_data.get('region'),
                                     city=self.cleaned_data.get('city'),
                                     school_name=self.cleaned_data.get('school_name'),
                                     phone=self.cleaned_data.get('phone'),
                                     nationality=self.cleaned_data.get('nationality'),
                                     document_type=self.cleaned_data.get('document_type'),
                                     document_number=self.cleaned_data.get('document_number'),
                                     )
        profile.current_class = self.cleaned_data.get('current_class')
        profile.save()
