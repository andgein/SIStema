from django.urls import path
from modules.study_results.staff import views as staff_views

app_name = 'study_results'

urlpatterns = [
    # Staff urls
    path('user/<int:user_id>/', staff_views.study_result_user, name='study_result_user'),
]
