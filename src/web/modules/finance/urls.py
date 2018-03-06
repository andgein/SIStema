from django.conf.urls import url

from . import views

app_name = 'finance'


urlpatterns = [
    url(r'^(?P<document_type>[^/]+)/$', views.download, name='download'),
    ]

