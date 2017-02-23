from django import forms

from frontend.forms import TextInputWithFaIcon, PasswordInputWithFaIcon


class CenteredForm(forms.Form):
    class Meta:
        show_fields = ()


class AuthForm(CenteredForm):
    email = forms.EmailField(required=True,
                             label='Электронная почта',
                             widget=TextInputWithFaIcon(attrs={
                                 'placeholder': 'Введите почту',
                                 'class': 'gui-input',
                                 'autofocus': 'autofocus',
                                 'fa': 'user',
                             }))

    password = forms.CharField(required=True,
                               label='Пароль',
                               widget=PasswordInputWithFaIcon(attrs={
                                   'placeholder': 'Введите пароль',
                                   'class': 'gui-input',
                                   'fa': 'lock',
                               }))

    remember_me = forms.BooleanField(required=False,
                                     initial=True,
                                     label='Запомнить меня',
                                     widget=forms.CheckboxInput())

    class Meta:
        show_fields = ('email', 'password')


class CompleteUserCreationForm(CenteredForm):
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

    email = forms.EmailField(required=True,
                             label='Электронная почта',
                             widget=TextInputWithFaIcon(attrs={
                                 'placeholder': 'Введите почту',
                                 'class': 'gui-input',
                                 'fa': 'envelope',
                             }))

    password = forms.CharField(required=True,
                               label='Пароль',
                               widget=PasswordInputWithFaIcon(attrs={
                                   'placeholder': 'Введите пароль',
                                   'class': 'gui-input',
                                   'fa': 'unlock-alt',
                               }))

    password_repeat = forms.CharField(required=True,
                                      label='Ещё раз',
                                      widget=PasswordInputWithFaIcon(attrs={
                                          'placeholder': 'Повторите пароль',
                                          'class': 'gui-input',
                                          'fa': 'lock'
                                      }))

    def clean_password_repeat(self):
        password = self.cleaned_data.get('password')
        password_repeat = self.cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            self._errors['password_repeat'] = self.error_class(['Пароли не совпадают'])

    class Meta:
        show_fields = ('first_name', 'last_name', 'email', 'password', 'password_repeat')


class RegistrationForm(CompleteUserCreationForm):
    remember_me = forms.BooleanField(required=False,
                                     initial=True,
                                     label='Запомнить меня',
                                     widget=forms.CheckboxInput())


class ForgotPasswordForm(CenteredForm):
    email = forms.CharField(required=True,
                            label='Электронная почта',
                            widget=TextInputWithFaIcon(attrs={
                                 'placeholder': 'Введите почту',
                                 'class': 'gui-input',
                                 'fa': 'envelope',
                             }))

    class Meta:
        show_fields = ('email', )


class PasswordRecoveryForm(CenteredForm):
    password = forms.CharField(required=True,
                               label='Новый пароль',
                               widget=PasswordInputWithFaIcon(attrs={
                                   'placeholder': 'Введите пароль',
                                   'class': 'gui-input',
                                   'fa': 'unlock-alt',
                               }))

    password_repeat = forms.CharField(required=True,
                                      label='Ещё раз',
                                      widget=PasswordInputWithFaIcon(attrs={
                                          'placeholder': 'Повторите пароль',
                                          'class': 'gui-input',
                                          'fa': 'lock'
                                      }))

    def clean_password_repeat(self):
        password = self.cleaned_data.get('password')
        password_repeat = self.cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            self._errors['password_repeat'] = self.error_class(['Пароли не совпадают'])

    class Meta:
        show_fields = ('password', 'password_repeat')
