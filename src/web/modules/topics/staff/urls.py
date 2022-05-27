from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^info/$', views.info, name='info'),
    url(r'^preview/$', views.preview, name='preview'),
    url(r'^reset_levels_cache/$', views.reset_levels_cache, name='reset_levels_cache'),
    url(r'^build_levels_cache/$', views.build_levels_cache, name='build_levels_cache'),
]
