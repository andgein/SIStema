from django.conf.urls import url, include

from users import views

urlpatterns = [
    url(r'^accounts/settings/$', views.account_settings, name='account_settings'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^user/', include([
        url(r'^profile$', views.profile, name='profile'),
    ], namespace='user')),
]
