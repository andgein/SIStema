from django.conf.urls import url
from modules.study_results.staff import views as staff_views

urlpatterns = [
    # Staff urls
    url(r'^$', staff_views.study_results, name='study_results'),
    url(r'^json/$', staff_views.study_results_json, name='study_results_json'),
]
