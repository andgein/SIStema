"""sistema URL Configuration"""
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'', include('home.urls')),
    url(r'^user/', include('users.urls', namespace='users')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^questionnaire/', include('questionnaire.urls')),
    url(r'^frontend/', include('frontend.urls', namespace='frontend')),
    url(r'^hijack/', include('hijack.urls')),
    url(r'^study-results/', include('modules.study_results.urls',
                                    namespace='study_results')),
    url(r'', include('schools.urls', namespace='school')),
]
