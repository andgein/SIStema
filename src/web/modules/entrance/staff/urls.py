from django.conf.urls import url
from django.urls import path

from . import views
from .export import ExportCompleteEnrollingTable

urlpatterns = [
    url(r'^enrolling/$', views.enrolling, name='enrolling'),
    url(r'^enrolling/data/$', views.enrolling_data, name='enrolling_data'),

    url(r'^enrolling/(?P<user_id>\d+)/$',
        views.enrolling_user,
        name='enrolling_user'),
    url(r'^enrolling/(?P<user_id>\d+)/profile/$',
        views.user_profile,
        name='user-profile'),
    url(r'^enrolling/(?P<user_id>\d+)/questionnaire/'
        '(?P<questionnaire_name>[^/]+)/$',
        views.user_questionnaire,
        name='user_questionnaire'),
    url(r'^enrolling/(?P<user_id>\d+)/topics/$',
        views.user_topics,
        name='user_topics'),
    url(r'^enrolling/export/$',
        ExportCompleteEnrollingTable.as_view(),
        name='export_complete_enrolling_table'),

    url(r'^solution/(?P<solution_id>\d+)/$',
        views.solution,
        name='user_solution'),

    url(r'^check/$', views.check, name='check'),
    url(r'^check/(?P<group_name>[^/]+)/$',
        views.check_group,
        name='check_group'),
    url(r'^check/(?P<group_name>[^/]+)/users/$',
        views.checking_group_users,
        name='checking_group_users'),
    url(r'^check/(?P<group_name>[^/]+)/checks/$',
        views.checking_group_checks,
        name='checking_group_checks'),
    url(r'^check/(?P<group_name>[^/]+)/task(?P<task_id>[^/]+)/$',
        views.check_task,
        name='check_task'),
    url(r'^check/(?P<group_name>[^/]+)/task(?P<task_id>[^/]+)/checks/$',
        views.task_checks,
        name='task_checks'),
    url(r'^check/(?P<group_name>[^/]+)/task(?P<task_id>[^/]+)/user(?P<user_id>[^/]+)/$',
        views.check_users_task,
        name='check_users_task'),
    url(r'^check/task(?P<task_id>[^/]+)/user(?P<user_id>[^/]+)/$',
        views.check_users_task,
        name='check_users_task'),

    url(r'^add_comment/user(?P<user_id>[^/]+)/$',
        views.add_comment,
        name='add_comment'),

    url(r'^initial/auto_reject/$',
        views.initial_auto_reject,
        name='initial.auto_reject'),

    path('enrollment_type/review/<int:user_id>',
         views.review_enrollment_type_for_user,
         name='enrollment_type_review_user')
]
