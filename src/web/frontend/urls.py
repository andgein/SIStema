from django.conf.urls import url

from . import views

app_name = 'frontend'

urlpatterns = [
    url(r'^table/(?P<table_name>[^/]+)/data/$', views.table_data, name='table_data'),
]
