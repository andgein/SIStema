from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.scans, name='scans'),
    url(r'^(?P<requirement_name>.+)/$', views.scan, name='scan')
]
