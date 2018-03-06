"""sistema URL Configuration"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

import wiki.urls
import django_nyt.urls


urlpatterns = [
    url(r'', include('home.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^ejudge/', include('modules.ejudge.urls', namespace='ejudge')),
    url(r'^questionnaire/', include('questionnaire.urls')),
    url(r'^frontend/', include('frontend.urls', namespace='frontend')),
    url(r'^poldnev/', include('modules.poldnev.urls', namespace='poldnev')),
    url(r'^study-results/', include('modules.study_results.urls',
                                    namespace='study_results')),
    url(r'^smartq/', include('modules.smartq.urls', namespace='smartq')),

    url(r'^hijack/', include('hijack.urls')),
    url(r'^notifications/', django_nyt.urls.get_pattern()),
    url(r'^wiki/', wiki.urls.get_pattern()),

    url(r'', include('users.urls')),
    url(r'', include('schools.urls', namespace='school')),
]


# Needed for django-wiki in the DEBUG mode as said at
# http://django-wiki.readthedocs.io/en/latest/installation.html#include-urlpatterns.
# According to
# https://docs.djangoproject.com/en/1.10/howto/static-files/#serving-files-uploaded-by-a-user-during-development
# it shoudn't have any effect outside of the DEBUG mode.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
