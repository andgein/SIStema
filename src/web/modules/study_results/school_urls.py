from django.urls import path
from modules.study_results.staff import views as staff_views

app_name = 'study_results'


urlpatterns = [
    # Staff urls
    path('', staff_views.study_results, name='view'),
    path('data/', staff_views.study_results_data, name='data'),
    path('upload/', staff_views.upload_study_results, name='upload'),
]
