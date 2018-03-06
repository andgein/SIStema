from django.conf.urls import url, include
from . import views
from .staff import views as staff_views

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

    # Submodules
    url(r'^scans/', include('modules.enrolled_scans.urls', namespace='enrolled_scans')),

    url(r'', include('modules.entrance.staff.urls')),
]
