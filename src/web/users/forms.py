from django import forms
from allauth.account import forms as account_forms
from allauth.account import adapter as account_adapter
from allauth.account import utils as account_utils

from django.utils.translation import ugettext_lazy as _
from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon


class CenteredForm(forms.Form):
    class Meta:
        show_fields = ()


class SignupForm(CenteredForm):
    first_name = forms.CharField(required=True,
                                 label='Имя',
                                 widget=TextInputWithFaIcon(attrs={
                                     'placeholder': 'Введите имя',
                                     'class': 'gui-input',
                                     'autofocus': 'autofocus',
                                     'fa': 'user',
                                 }))

    last_name = forms.CharField(required=True,
                                label='Фамилия',
                                widget=TextInputWithFaIcon(attrs={
                                    'placeholder': 'Введите фамилию',
                                    'class': 'gui-input',
                                    'fa': 'user',
                                }))

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
