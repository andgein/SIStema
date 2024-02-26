from django.urls import path, include

from schools import views

app_name = 'schools'

urlpatterns = [
    path('<str:school_name>/', include([
        path('', views.index, name='index'),
        path('user/', views.user, name='user'),
        path('staff/', views.staff, name='staff'),
        path('questionnaire/<str:questionnaire_name>/',
             views.questionnaire,
             name='questionnaire'),
        path('groups/', include('groups.school_urls', namespace='groups')),

        # Modules
        path('entrance/', include('modules.entrance.urls', namespace='entrance')),
        path('topics/', include('modules.topics.urls', namespace='topics')),
        path('finance/', include('modules.finance.urls', namespace='finance')),
        path('study-results/', include('modules.study_results.school_urls',
                                       namespace='study_results')),
        path('ejudge/', include('modules.ejudge.school_urls',
                                namespace='ejudge')),
    ])),
]
