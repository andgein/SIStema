from django.urls import path, include
from modules.smartq import views

app_name = 'smartq'

urlpatterns = [
    path('<slug:question_short_name>/', include([
        path('',
             views.show_admin_question_instance,
             name='show_admin_question_instance'),
        path('regenerate/',
             views.regenerate_admin_question_instance,
             name='regenerate_admin_question_instance'),
    ])),
    path('save-answer/<int:generated_question_id>/',
         views.save_answer,
         name='save_answer'),
]
