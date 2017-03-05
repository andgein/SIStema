from django import shortcuts
from django.contrib.auth import decorators as auth_decorators
from sistema import decorators as sistema_decorators
from users import forms, models


@auth_decorators.login_required()
def account_settings(request):
    return shortcuts.render(request, 'users/account_settings.html')


def _init_profile_form(request):
    if request.user_profile:
        result = {}
        for field_name in models.UserProfile.get_field_names():
            result[field_name] = getattr(request.user_profile, field_name)
        return result
    return {'first_name': request.user.first_name,
            'last_name': request.user.last_name}


@auth_decorators.login_required()
@sistema_decorators.form_handler('users/profile.html',
                                 forms.UserProfileForm,
                                 _init_profile_form)
def profile(request, form):
    if request.user_profile:
        user_profile = request.user_profile
    else:
        user_profile = models.UserProfile.objects.create(user=request.user)
    for field_name in user_profile.get_field_names():
        setattr(user_profile, field_name, form.cleaned_data.get(field_name))
    user_profile.save()
