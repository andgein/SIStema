from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^exam/$', views.exam, name='exam'),
    url(r'^exam/solution/(?P<solution_id>\d+)/', views.solution, name='solution'),
    url(r'^exam/submit/(?P<task_id>\d+)/', views.submit, name='submit'),
    url(r'^exam/upgrade/', views.upgrade, name='upgrade'),
    ]
