from django.conf.urls import url, include

from users import views

urlpatterns = [
    url(r'^accounts/settings/$', views.account_settings, name='account_settings'),
    url(r'^accounts/find-similar/$', views.find_similar_accounts, name='account_find_similar'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^user/profile$', views.profile, name='user-profile'),
]
