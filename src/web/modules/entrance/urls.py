from django.conf.urls import url, include
from . import views
from .staff import views as staff_views

urlpatterns = [
    url(r'^exam/$', views.exam, name='exam'),
    url(r'^exam/solution/(?P<solution_id>\d+)/$', views.solution, name='solution'),
    url(r'^exam/task/(?P<task_id>\d+)/$', views.task, name='task'),
    url(r'^exam/task/(?P<task_id>\d+)/submit/$', views.submit, name='submit'),
    url(r'^exam/task/(?P<task_id>\d+)/submits/$', views.task_solutions, name='task_solutions'),
    url(r'^exam/upgrade_panel/$', views.upgrade_panel, name='upgrade_panel'),
    url(r'^exam/upgrade/$', views.upgrade, name='upgrade'),

    url(r'^results/$', views.results, name='results'),

    # Submodules
    url(r'^scans/', include('modules.enrolled_scans.urls', namespace='enrolled_scans')),

    # Staff urls
    url(r'^enrolling/$', staff_views.enrolling, name='enrolling'),
    url(r'^enrolling/(?P<user_id>\d+)/$', staff_views.enrolling_user, name='enrolling_user'),
    url(r'^enrolling/(?P<user_id>\d+)/profile/$', staff_views.user_profile, name='user_profile'),
    url(r'^enrolling/(?P<user_id>\d+)/questionnaire/(?P<questionnaire_name>[^/]+)/$', staff_views.user_questionnaire, name='user_questionnaire'),
    url(r'^enrolling/(?P<user_id>\d+)/topics/$', staff_views.user_topics, name='user_topics'),
    url(r'^enrolling/(?P<user_id>\d+)/change_group/$', staff_views.change_group, name='change_group'),

    url(r'^check/$', staff_views.check, name='check'),
    url(r'^check/(?P<group_name>[^/]+)/$', staff_views.check_group, name='check_group'),
    url(r'^check/(?P<group_name>[^/]+)/users/$', staff_views.checking_group_users, name='checking_group_users'),
    url(r'^check/(?P<group_name>[^/]+)/checks/$', staff_views.checking_group_checks, name='checking_group_checks'),
    url(r'^check/(?P<group_name>[^/]+)/task(?P<task_id>[^/]+)/$', staff_views.check_task, name='check_task'),
    url(r'^check/(?P<group_name>[^/]+)/task(?P<task_id>[^/]+)/checks/$', staff_views.task_checks, name='task_checks'),
    url(r'^check/(?P<group_name>[^/]+)/task(?P<task_id>[^/]+)/user(?P<user_id>[^/]+)/$', staff_views.check_users_task, name='check_users_task'),
    url(r'^check/task(?P<task_id>[^/]+)/user(?P<user_id>[^/]+)/$', staff_views.check_users_task, name='check_users_task'),
    url(r'^solution/(?P<solution_id>\d+)/$', staff_views.solution, name='user_solution'),

    url(r'^initial/auto_reject/$', staff_views.initial_auto_reject, name='initial.auto_reject'),
    url(r'^initial/checking_groups/$', staff_views.initial_checking_groups, name='initial.checking_groups'),
    ]
