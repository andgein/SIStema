from django.views.decorators import http as http_decorators
from django import shortcuts
from django.contrib.auth import decorators as auth_decorators
from sistema import decorators as sistema_decorators
from users import forms, models, search_utils


@auth_decorators.login_required()
def account_settings(request):
    return shortcuts.render(request, 'users/account_settings.html')


@http_decorators.require_POST
def find_similar_accounts(request):
    form = forms.UserProfileForm(data=request.POST)
    form.full_clean()
    users = search_utils.SimilarAccountSearcher(form.fill_user_profile(request)).search()
    return shortcuts.render(request, 'account/_similar_accounts.html', {'users': users})


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
    form.fill_user_profile(request).save()
