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
    url(r'^user/', include([
        url(r'^profile/$', views.profile, name='profile'),
    ], namespace='user')),
    url(r'^users/admin/', include(admin_urlpatterns, namespace='users_admin')),
]
