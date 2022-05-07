from django.conf.urls import url
from modules.study_results.staff import views as staff_views

app_name = 'study_results'


urlpatterns = [
    # Staff urls
    url(r'^$', staff_views.study_results, name='view'),
    url(r'^data/$', staff_views.study_results_data, name='data'),
    url(r'^upload$', staff_views.upload_study_results, name='upload'),
]
