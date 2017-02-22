from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<questionnaire_name>[^/]+)/reset/$', views.reset, name='reset'),
    url(r'^(?P<questionnaire_name>[^/]+)/$', views.questionnaire, name='questionnaire'),
    ]

