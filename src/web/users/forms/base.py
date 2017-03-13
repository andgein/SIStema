import enum

from django import forms

from users import models


class AccountBaseForm(forms.Form):
    class Tab(enum.Enum):
        NONE = 0,
        LOGIN = 1,
        SIGNUP = 2,

    def __init__(self, *args, **kwargs):
        self.__active_tab = kwargs.pop('active_tab')
        super().__init__(*args, **kwargs)

    def login_is_active(self):
        return self.__active_tab == AccountBaseForm.Tab.LOGIN

    def signup_is_active(self):
        return self.__active_tab == AccountBaseForm.Tab.SIGNUP


def _signup(form, user):
    profile = models.UserProfile(user=user)
    for field_name in profile.get_field_names():
        setattr(profile, field_name, form.cleaned_data.get(field_name))
    profile.save()


# NOTE you can not load allauth.account.forms before this class
# (because it is a base class for allauth.account.forms.SignupForm)
class BaseSignupForm(AccountBaseForm):
    def signup(self, request, user):  # TODO check can delete 'request'
        if hasattr(self, 'sociallogin'):
            user.set_password(self.cleaned_data.get('password1'))
        _signup(self, user)
