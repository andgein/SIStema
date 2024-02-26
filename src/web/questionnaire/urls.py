from django import conf
from django.urls import path

from . import views

app_name = 'questionnaire'


urlpatterns = [
    path('<str:questionnaire_name>/', views.questionnaire, name='questionnaire'),
]

if conf.settings.DEBUG:
    urlpatterns += [
        path('<str:questionnaire_name>/reset/', views.reset, name='reset'),
    ]
