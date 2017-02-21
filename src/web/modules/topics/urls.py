from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^reset/$', views.reset, name='reset'),
    url(r'^finish/$', views.finish, name='finish'),
    url(r'^correcting/(?P<topic_name>[^/]+)/$', views.correcting_topic_marks, name='correcting_topic'),
    ]
