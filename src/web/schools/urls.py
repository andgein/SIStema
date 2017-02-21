from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^(?P<school_name>[^/]+)/', include([
        url(r'^$', views.index, name='index'),
        url(r'^questionnaire/(?P<questionnaire_name>[^/]+)/',
            views.questionnaire,
            name='questionnaire'),
        # Modules
        url(r'^entrance/', include('modules.entrance.urls', namespace='entrance')),
        url(r'^topics/', include('modules.topics.urls', namespace='topics')),
        url(r'^finance/', include('modules.finance.urls', namespace='finance')),
    ])),
]
