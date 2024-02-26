from django.urls import path

from . import views

app_name = 'finance'


urlpatterns = [
    path('<str:document_type>/', views.download, name='download'),
    ]

