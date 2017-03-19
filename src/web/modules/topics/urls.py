from django import conf
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^check-topics/$', views.check_topics, name='check_topics'),
    url(r'^check-topics/return/$', views.return_to_correcting, name='return_to_correcting'),
    url(r'^check-topics/finish/$', views.finish_smartq, name='finish_smartq'),
    url(r'^finish/$', views.finish, name='finish'),
    url(r'^correcting/(?P<topic_name>[^/]+)/$', views.correcting_topic_marks, name='correcting_topic'),
    url(r'^start-checking/$', views.start_checking, name='start_checking'),
]

if conf.settings.DEBUG:
    urlpatterns += [
        url(r'^reset/$', views.reset, name='reset'),
    ]
