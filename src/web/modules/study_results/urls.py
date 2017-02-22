from django.conf.urls import url
from modules.study_results.staff import views as staff_views

urlpatterns = [
    # Staff urls
    url(r'^user/(?P<user_id>\d+)/$',
        staff_views.study_result_user, name='study_result_user'),
]
