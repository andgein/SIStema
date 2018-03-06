from django.conf.urls import include, url

from modules.ejudge import views

app_name = 'ejudge'


admin_urlpatterns = [
    url(r'^submission-autocomplete/$',
        views.SubmissionAutocomplete.as_view(),
        name='submission-autocomplete'),
    url(r'^solution-checking-result-autocomplete/$',
        views.SolutionCheckingResultAutocomplete.as_view(),
        name='solution-checking-result-autocomplete'),
]


urlpatterns = [
    url(r'^admin/', include(admin_urlpatterns)),
]
