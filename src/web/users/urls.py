from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^register/', views.register, name='register'),
    url(r'^complete/$', views.complete, name='complete'),
    url(r'^confirm/(?P<token>[^/]+)', views.confirm, name='confirm'),

    url(r'^forget/$', views.forget, name='forget'),
    url(r'^recover/(?P<token>[^/]+)', views.recover, name='recover'),

    url('', include('social_django.urls', namespace='social')),
]
