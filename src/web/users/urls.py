from django.conf.urls import url, include

from users import views
import users.admin.urls as admin_urls


user_urlpatterns = [
    url(r'^profile/$', views.profile, name='profile'),
]


urlpatterns = [
    url(r'^accounts/settings/$',
        views.account_settings,
        name='account_settings'),
    url(r'^accounts/find-similar/$',
        views.find_similar_accounts,
        name='account_find_similar'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^user/', include(user_urlpatterns, namespace='user')),
    url(r'^users/admin/',
        include(admin_urls.urlpatterns, namespace='users_admin')),
]
