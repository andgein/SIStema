from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^user/$', views.user, name='user'),
    url(r'^staff/$', views.staff, name='staff'),
]
