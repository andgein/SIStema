from django.conf.urls import url
from modules.study_results.staff import views as staff_views

urlpatterns = [
    # Staff urls
    url(r'^$', staff_views.study_results, name='study_results'),
    url(r'^(?P<school_name>[^/]+)/$',
        staff_views.study_results_school, name='study_results_school'),
    url(r'^(?P<school_name>[^/]+)/user/(?P<user_id>\d+)/$',
        staff_views.study_result_user, name='study_result_user'),
]
