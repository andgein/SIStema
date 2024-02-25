from django import conf
from django.urls import path, include

from . import views

app_name = 'topics'


urlpatterns = [
    path('', views.index, name='index'),
    path('checking/', views.check_topics, name='check_topics'),
    path('checking/start/', views.start_checking, name='start_checking'),
    path('checking/return/', views.return_to_correcting, name='return_to_correcting'),
    path('checking/finish/', views.finish_smartq, name='finish_smartq'),
    path('finish/', views.finish, name='finish'),
    path('correcting/<slug:topic_name>/', views.correcting_topic_marks, name='correcting_topic'),
    path('', include('modules.topics.staff.urls')),
]

if conf.settings.DEBUG:
    urlpatterns += [
        path('reset/', views.reset, name='reset'),
    ]
