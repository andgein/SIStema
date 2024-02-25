"""sistema URL Configuration"""
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    path('', include('home.urls')),
    path('admin/', admin.site.urls),
    path('questionnaire/', include('questionnaire.urls')),
    path('frontend/', include('frontend.urls', namespace='frontend')),
    path('groups/', include('groups.urls', namespace='groups')),
    path('poldnev/', include('modules.poldnev.urls', namespace='poldnev')),
    path('study-results/', include('modules.study_results.urls',
                                   namespace='study_results')),
    path('smartq/', include('modules.smartq.urls', namespace='smartq')),

    path('hijack/', include('hijack.urls')),
    path('notifications/', include('django_nyt.urls')),
    path('wiki/', include('wiki.urls')),
    path('__debug__/', include('debug_toolbar.urls')),

    path('', include('users.urls')),
    path('', include('schools.urls', namespace='school')),

]

if settings.DEBUG:
    urlpatterns.insert(1, path('silk/', include('silk.urls', namespace='silk')))

# Needed for django-wiki in the DEBUG mode as said at
# http://django-wiki.readthedocs.io/en/latest/installation.html#include-urlpatterns.
# According to
# https://docs.djangoproject.com/en/1.10/howto/static-files/#serving-files-uploaded-by-a-user-during-development
# it shouldn't have any effect outside the DEBUG mode.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
