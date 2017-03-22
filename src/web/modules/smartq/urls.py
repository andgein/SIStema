from django.conf.urls import url, include
from modules.smartq import views

urlpatterns = [
    url(r'^(?P<question_short_name>[^/]+)/', include([
        url(r'^$',
            views.show_admin_question_instance,
            name='show_admin_question_instance'),
        url(r'^regenerate/$',
            views.regenerate_admin_question_instance,
            name='regenerate_admin_question_instance'),
    ])),
    url(r'save-answer/(?P<generated_question_id>[^/]+)/$',
        views.save_answer,
        name='save_answer'),
]
