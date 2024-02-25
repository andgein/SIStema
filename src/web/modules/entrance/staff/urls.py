from django.urls import path

from . import views
from .export import ExportCompleteEnrollingTable

urlpatterns = [
    path('enrolling/', views.enrolling, name='enrolling'),
    path('enrolling/data/', views.enrolling_data, name='enrolling_data'),

    path('enrolling/<int:user_id>/', views.enrolling_user, name='enrolling_user'),
    path('enrolling/<int:user_id>/profile/', views.user_profile, name='user-profile'),
    path('enrolling/<int:user_id>/questionnaire/<slug:questionnaire_name>/',
         views.user_questionnaire,
         name='user_questionnaire'),
    path('enrolling/<int:user_id>/topics/', views.user_topics, name='user_topics'),
    path('enrolling/export/', ExportCompleteEnrollingTable.as_view(), name='export_complete_enrolling_table'),

    path('solution/<int:solution_id>/', views.solution, name='user_solution'),

    path('check/', views.check, name='check'),
    path('check/<slug:group_name>/', views.check_group, name='check_group'),
    path('check/<slug:group_name>/users/', views.checking_group_users, name='checking_group_users'),
    path('check/<slug:group_name>/teachers/', views.checking_group_teachers, name='checking_group_teachers'),
    path('check/<slug:group_name>/teacher<int:teacher_id>/checks/',
         views.teacher_checks,
         name='teacher_checks'),
    path('check/<slug:group_name>/teacher<int:teacher_id>/task<int:task_id>/checks/',
         views.teacher_task_checks,
         name='teacher_task_checks'),
    path('check/<slug:group_name>/checks/',
         views.checking_group_checks,
         name='checking_group_checks'),
    path('check/<slug:group_name>/task<int:task_id>',
         views.check_task,
         name='check_task'),
    path('check/<slug:group_name>/task<int:task_id>/checks/',
         views.task_checks,
         name='task_checks'),
    path('check/<slug:group_name>/task<int:task_id>/user<int:user_id>/',
         views.check_users_task,
         name='check_users_task'),
    path('check/task<int:task_id>/user<int:user_id>/',
         views.check_users_task,
         name='check_users_task'),

    path('add_comment/user<int:user_id>/',
         views.add_comment,
         name='add_comment'),

    path('initial/auto_reject/',
         views.initial_auto_reject,
         name='initial.auto_reject'),

    path('enrollment_type/review/<int:user_id>',
         views.review_enrollment_type_for_user,
         name='enrollment_type_review_user')
]
