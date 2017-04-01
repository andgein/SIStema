from django.conf.urls import include, url

from modules.ejudge.staff import views as staff_views
from modules.ejudge import views


admin_urlpatterns = [
    url(r'^submission-autocomplete/$',
        views.SubmissionAutocomplete.as_view(),
        name='submission-autocomplete'),
    url(r'^solution-checking-result-autocomplete/$',
        views.SolutionCheckingResultAutocomplete.as_view(),
        name='solution-checking-result-autocomplete'),
]


urlpatterns = [
    url(r'^admin/', include(admin_urlpatterns, namespace='admin')),
    # Staff urls from school
    url(r'^stats/$', staff_views.show_ejudge_stats, name='show_ejudge_stats'),
]
