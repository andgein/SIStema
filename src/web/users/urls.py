from django.conf.urls import url, include

from users import views

admin_urlpatterns = [
    url(r'^user-autocomplete/$',
        views.UserAutocomplete.as_view(),
        name='user-autocomplete'),
]

urlpatterns = [
    url(r'^accounts/settings/$', views.account_settings, name='account_settings'),
    url(r'^accounts/find-similar/$', views.find_similar_accounts, name='account_find_similar'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^user/profile$', views.profile, name='user-profile'),
    url(r'^users/admin/', include(admin_urlpatterns)),
]
