from django import shortcuts
from django.contrib.auth import decorators as auth_decorators
from django.template.loader import render_to_string
from django.views.decorators import http as http_decorators
import django.http

from users import forms
from users import models
from users import search_utils


@auth_decorators.login_required()
def account_settings(request):
    return shortcuts.render(request, 'users/account_settings.html')


def _render_user_account(user):
    return render_to_string('account/_similar_account.html', {'user': user})


@http_decorators.require_POST
def find_similar_accounts(request):
    form = forms.UserProfileForm(all_fields_are_required=False, data=request.POST)
    form.full_clean()
    users = search_utils.SimilarAccountSearcher(form.fill_user_profile(request.user)).search()
    return django.http.JsonResponse({user.id: _render_user_account(user) for user in users})


def profile_for_user(request, user):
    all_fields_are_required = request.GET.get('full', False)

    if request.method == 'POST':
        form = forms.UserProfileForm(all_fields_are_required=all_fields_are_required, data=request.POST)
        if form.is_valid():
            form.fill_user_profile(user).save()
            return shortcuts.redirect('home')
    else:
        if hasattr(user, 'profile'):
            initial_data = {}
            for field_name in models.UserProfile.get_field_names():
                initial_data[field_name] = getattr(user.profile, field_name)
        else:
            initial_data = {'first_name': user.first_name,
                            'last_name': user.last_name}
        form = forms.UserProfileForm(all_fields_are_required=all_fields_are_required,
                                     initial=initial_data)

    return shortcuts.render(request, 'users/profile.html',
                            {'form': form,
                             'is_creating': not hasattr(user, 'profile'),
                             'is_confirming': request.GET.get('confirm', False)})


@auth_decorators.login_required()
def profile(request):
    return profile_for_user(request, request.user)
