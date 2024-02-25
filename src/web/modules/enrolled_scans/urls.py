from django.urls import path
from . import views

app_name = 'enrolled_scans'

urlpatterns = [
    path('', views.scans, name='scans'),
    path('<requirement_name>/', views.scan, name='scan')
]
