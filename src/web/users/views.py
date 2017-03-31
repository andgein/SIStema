from django import shortcuts
from django.contrib.auth import decorators as auth_decorators
from django.db.models import Q
from django.template.loader import render_to_string
from django.views.decorators import http as http_decorators
import django.contrib.admin.views.decorators as admin_decorators
import django.http
import django.utils.decorators as utils_decorators

from dal import autocomplete

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
    form = forms.UserProfileForm(data=request.POST)
    form.full_clean()
    users = search_utils.SimilarAccountSearcher(form.fill_user_profile(request.user)).search()
    return django.http.JsonResponse({user.id: _render_user_account(user) for user in users})


def profile_for_user(request, user):
    if request.method == 'POST':
        form = forms.UserProfileForm(data=request.POST)
        if form.is_valid():
            form.fill_user_profile(user).save()
            return shortcuts.redirect('home')
        return shortcuts.render(request, 'users/profile.html', {'form': form})
    else:
        if hasattr(user, 'profile'):
            initial_data = {}
            for field_name in models.UserProfile.get_field_names():
                initial_data[field_name] = getattr(user.profile, field_name)
        else:
            initial_data = {'first_name': user.first_name,
                            'last_name': user.last_name}
        form = forms.UserProfileForm(initial=initial_data)
        return shortcuts.render(request, 'users/profile.html',
                                {'form': form,
                                 'is_creating': not hasattr(user, 'profile'),
                                 'is_confirming': request.GET.get('confirm', False)})


@auth_decorators.login_required()
def profile(request):
    return profile_for_user(request, request.user)


@utils_decorators.method_decorator(admin_decorators.staff_member_required,
                                   name='dispatch')
class UserAutocomplete(autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        super().__init__(model=models.User, **kwargs)

    def get_queryset(self):
        qs = models.User.objects.all()

        if self.q.isdigit():
            qs = qs.filter(id=int(self.q))
        elif self.q:
            for token in self.q.strip().split(' '):
                qs = qs.filter(Q(first_name__icontains=token) |
                               Q(last_name__icontains=token) |
                               Q(user_profile__first_name__icontains=token) |
                               Q(user_profile__middle_name__icontains=token) |
                               Q(user_profile__last_name__icontains=token))

        return qs
