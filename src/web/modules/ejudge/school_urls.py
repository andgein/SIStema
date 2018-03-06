from django.conf.urls import url

from modules.ejudge.staff import views as staff_views

app_name = 'ejudge'


urlpatterns = [
    url(r'^stats/$', staff_views.show_ejudge_stats, name='show_ejudge_stats'),
]
