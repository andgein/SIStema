from django.urls import path

from modules.ejudge.staff import views as staff_views

app_name = 'ejudge'


urlpatterns = [
    path('stats/', staff_views.show_ejudge_stats, name='show_ejudge_stats'),
]
