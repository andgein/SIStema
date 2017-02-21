from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<document_type>[^/]+)/$', views.download, name='download'),
    ]

