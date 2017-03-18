from django import shortcuts
from django.contrib import auth
import django.http
import django.views.decorators.http as http_decorators

from modules.smartq import models
import sistema.staff

@sistema.staff.only_staff
def show_admin_question_instance(request, question_short_name):
    base_question = shortcuts.get_object_or_404(models.Question,
                                                short_name=question_short_name)

    generated_question = models.StaffGeneratedQuestion.get_instance(
        request.user, base_question)

    status_lines = []

    if request.method == 'POST':
        result = generated_question.check_answer(request.POST)
        status_lines = [str(result.status)]
        if result.message:
            status_lines.append('  message: {}'.format(result.message))
        for name, value in result.field_messages.items():
            status_lines.append('  {}: {}'.format(name, value))

    return shortcuts.render(request, 'smartq/staff/test_question.html', {
        'question': generated_question,
        'status_lines': status_lines,
    })

@sistema.staff.only_staff
@http_decorators.require_POST
def regenerate_admin_question_instance(request, question_short_name):
    base_question = shortcuts.get_object_or_404(models.Question,
                                                short_name=question_short_name)

    models.StaffGeneratedQuestion.regenerate(request.user, base_question)

    return shortcuts.redirect('smartq:show_admin_question_instance',
                              question_short_name=question_short_name)

@auth.decorators.login_required
@http_decorators.require_POST
def save_answer(request, generated_question_id):
    generated_question = shortcuts.get_object_or_404(models.GeneratedQuestion,
                                                     id=generated_question_id,
                                                     user=request.user)
    generated_question.save_answer(request.POST)
    return django.http.JsonResponse({'status': 'ok'})
