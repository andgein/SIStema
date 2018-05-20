from django.conf.urls import url, include

from . import views

app_name = 'entrance'

urlpatterns = [
    url(r'^exam/$', views.exam, name='exam'),
    url(r'^exam/solution/(?P<solution_id>\d+)/$', views.solution, name='solution'),
    url(r'^exam/task/(?P<task_id>\d+)/$', views.task, name='task'),
    url(r'^exam/task/(?P<task_id>\d+)/submit/$', views.submit, name='submit'),
    url(r'^exam/task/(?P<task_id>\d+)/submits/$', views.task_solutions, name='task_solutions'),
    url(r'^exam/upgrade_panel/$', views.upgrade_panel, name='upgrade_panel'),
    url(r'^exam/upgrade/$', views.upgrade, name='upgrade'),

    url(r'^results/$', views.results, name='results'),
    url(r'^results/data/$', views.results_data, name='results_data'),

    url(r'^steps/(?P<step_id>\d+)/', include(([
        url(r'^set_enrollment_type/$', views.set_enrollment_type, name='set_enrollment_type'),
        url(r'^reset_enrollment_type/$', views.reset_enrollment_type, name='reset_enrollment_type'),

        url(r'^select_session_and_parallel/$', views.select_session_and_parallel, name='select_session_and_parallel'),
        url(r'^reset_session_and_parallel/$', views.reset_session_and_parallel, name='reset_session_and_parallel'),
        url(r'^approve_enrollment/$', views.approve_enrollment, name='approve_enrollment'),
        url(r'^reject_participation/$', views.reject_participation, name='reject_participation'),
    ], 'steps'), namespace='steps')),

    # Submodules
    url(r'^scans/', include('modules.enrolled_scans.urls', namespace='enrolled_scans')),

    url(r'', include('modules.entrance.staff.urls')),
]
