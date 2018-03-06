from django import conf
from django.conf.urls import url

from . import views

app_name = 'questionnaire'


urlpatterns = [
    url(r'^(?P<questionnaire_name>[^/]+)/$', views.questionnaire, name='questionnaire'),
]

if conf.settings.DEBUG:
    urlpatterns += [
        url(r'^(?P<questionnaire_name>[^/]+)/reset/$', views.reset, name='reset'),
    ]
