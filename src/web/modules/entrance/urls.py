from django.urls import path, include

from . import views

app_name = 'entrance'

urlpatterns = [
    path('exam/', views.exam, name='exam'),
    path('exam/solution/<int:solution_id>/', views.solution, name='solution'),
    path('exam/task/<int:task_id>/', views.task, name='task'),
    path('exam/task/<int:task_id>/submit/', views.submit, name='submit'),
    path('exam/task/<int:task_id>/submits/', views.task_solutions, name='task_solutions'),
    path('exam/upgrade_panel/', views.upgrade_panel, name='upgrade_panel'),
    path('exam/upgrade/', views.upgrade, name='upgrade'),

    path('results/', views.results, name='results'),
    path('results/data/', views.results_data, name='results_data'),

    path('steps/<int:step_id>/', include(([
        path('set_enrollment_type/', views.set_enrollment_type, name='set_enrollment_type'),
        path('reset_enrollment_type/', views.reset_enrollment_type, name='reset_enrollment_type'),

        path('select_entrance_level/', views.select_entrance_level, name='select_entrance_level'),

        path('select_session_and_parallel/', views.select_session_and_parallel, name='select_session_and_parallel'),
        path('reset_session_and_parallel/', views.reset_session_and_parallel, name='reset_session_and_parallel'),
        path('approve_enrollment/', views.approve_enrollment, name='approve_enrollment'),
        path('reject_participation/', views.reject_participation, name='reject_participation'),
    ], 'steps'), namespace='steps')),

    # Submodules
    path('scans/', include('modules.enrolled_scans.urls', namespace='enrolled_scans')),

    path('', include('modules.entrance.staff.urls')),
]
