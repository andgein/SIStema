from django.urls import path

from . import views

app_name = 'frontend'

urlpatterns = [
    path('table/<table_name>/data/', views.table_data, name='table_data'),
]
