from django import conf
from django.conf.urls import url
from . import views

app_name = 'topics'


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^checking/$', views.check_topics, name='check_topics'),
    url(r'^checking/start/$', views.start_checking, name='start_checking'),
    url(r'^checking/return/$', views.return_to_correcting, name='return_to_correcting'),
    url(r'^checking/finish/$', views.finish_smartq, name='finish_smartq'),
    url(r'^finish/$', views.finish, name='finish'),
    url(r'^correcting/(?P<topic_name>[^/]+)/$', views.correcting_topic_marks, name='correcting_topic'),
]

if conf.settings.DEBUG:
    urlpatterns += [
        url(r'^reset/$', views.reset, name='reset'),
    ]
