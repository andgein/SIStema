from django.conf.urls import url, include

from schools import views

urlpatterns = [
    url(r'^(?P<school_name>[^/]+)/', include([
        url(r'^$', views.index, name='index'),
        url(r'^user/$', views.user, name='user'),
        url(r'^staff/$', views.staff, name='staff'),
        url(r'^questionnaire/(?P<questionnaire_name>[^/]+)/$',
            views.questionnaire,
            name='questionnaire'),

        # Modules
        url(r'^entrance/', include('modules.entrance.urls', namespace='entrance')),
        url(r'^topics/', include('modules.topics.urls', namespace='topics')),
        url(r'^finance/', include('modules.finance.urls', namespace='finance')),
        url(r'^study-results/', include('modules.study_results.school_urls',
                                        namespace='study_results')),
        url(r'^ejudge/', include('modules.ejudge.urls',
                                 namespace='ejudge')),
    ])),
]
