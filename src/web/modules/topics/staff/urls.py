from django.urls import path

from . import views

urlpatterns = [
    path('info/', views.info, name='info'),
    path('preview/', views.preview, name='preview'),
    path('reset_levels_cache/', views.reset_levels_cache, name='reset_levels_cache'),
    path('build_levels_cache/', views.build_levels_cache, name='build_levels_cache'),
]
