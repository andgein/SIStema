from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^info/$', views.info, name='info'),
    url(r'^preview/$', views.preview, name='preview'),
]
