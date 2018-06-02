import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import render, get_object_or_404, redirect

from . import forms
from . import models


@transaction.atomic
def save_questionnaire_answers(user, questionnaire, form):
    # Remove all old answers
    models.QuestionnaireAnswer.objects.filter(questionnaire=questionnaire,
                                              user=user).delete()

    for field in form.fields:
        answer = form.cleaned_data[field]
        if isinstance(answer, (tuple, list)):
            answer_list = answer
        elif isinstance(answer, (datetime.date, datetime.datetime)):
            answer_list = [answer.strftime(
                settings.SISTEMA_QUESTIONNAIRE_STORING_DATE_FORMAT)]
        elif answer is None:  # For not-filled dates i.e.
            answer_list = []
        elif isinstance(answer, QuerySet):
            answer_list = answer.values_list('pk', flat=True)
        else:
            answer_list = [answer]

        for answer in answer_list:
            models.QuestionnaireAnswer(questionnaire=questionnaire,
                                       user=user,
                                       question_short_name=field,
                                       answer=answer
                                       ).save()

    models.UserQuestionnaireStatus.objects.update_or_create(
        questionnaire=questionnaire,
        user=user,
        defaults={
            'status': models.UserQuestionnaireStatus.Status.FILLED
        },
    )


def _get_user_questionnaire_answers(user, questionnaire):
    questions = {q.short_name: q for q in questionnaire.questions}
    answers = models.QuestionnaireAnswer.objects.filter(user=user, questionnaire=questionnaire)

    # TODO: refactor this
    result = {}
    for answer in answers:
        # Question could be deleted from the time when user answered it
        if answer.question_short_name not in questions:
            continue
        if isinstance(questions[answer.question_short_name], models.ChoiceQuestionnaireQuestion) and \
                questions[answer.question_short_name].is_multiple:
            if answer.question_short_name not in result:
                result[answer.question_short_name] = []
            result[answer.question_short_name].append(answer.answer)
        elif isinstance(questions[answer.question_short_name], models.DateQuestionnaireQuestion):
            result[answer.question_short_name] = datetime.datetime.strptime(
                answer.answer,
                settings.SISTEMA_QUESTIONNAIRE_STORING_DATE_FORMAT
            ).date()
        elif isinstance(questions[answer.question_short_name],
                        models.UserListQuestionnaireQuestion):
            if answer.question_short_name not in result:
                result[answer.question_short_name] = []
            result[answer.question_short_name].append(answer.answer)
        else:
            result[answer.question_short_name] = answer.answer

    return result


def questionnaire_for_user(request, user, questionnaire_name):
    if hasattr(request, 'school'):
        qs = (models.Questionnaire.objects
              .filter(school=request.school, short_name=questionnaire_name))
        # If questionnaire with this name exists for the school, use it,
        # otherwise use common questionnaire (with school = None)
        if qs.exists():
            questionnaire = qs.first()
        else:
            questionnaire = get_object_or_404(models.Questionnaire,
                                              school__isnull=True,
                                              short_name=questionnaire_name)
    else:
        questionnaire = get_object_or_404(models.Questionnaire,
                                          school__isnull=True,
                                          short_name=questionnaire_name)

    form_class = questionnaire.get_form_class(user)

    # There are no closed questionnaires for staff users
    is_closed = (questionnaire.is_closed_for_user(user) and
                 not request.user.is_staff)

    # Typing dynamics form
    typing_dynamics_form = None
    if questionnaire.should_record_typing_dynamics and request.user == user:
        # We record typing dynamics only in the case when questionnaire is
        # filled by the user himself, but not by admin.
        if request.method == 'POST':
            typing_dynamics_form = forms.QuestionnaireTypingDynamicsForm(
                data=request.POST)
            if typing_dynamics_form.is_valid():
                # TODO(artemtab): validate JSON
                models.QuestionnaireTypingDynamics.objects.create(
                    user=user,
                    questionnaire=questionnaire,
                    typing_data=typing_dynamics_form.cleaned_data['typing_data'],
                )
            else:
                # TODO(artemtab): most probably the typing data is too large.
                #                 Log some error?
                pass
        else:
            typing_dynamics_form = forms.QuestionnaireTypingDynamicsForm()

    # Main questionnaire form
    questionnaire_answers = (
        _get_user_questionnaire_answers(user, questionnaire) or None)
    if request.method == 'POST':
        form = form_class(data=request.POST, initial=questionnaire_answers)
        if is_closed:
            form.add_error(None, 'Время заполнения анкеты вышло')
        elif form.is_valid():
            save_questionnaire_answers(user, questionnaire, form)
            if questionnaire.school is not None:
                return redirect(questionnaire.school)
            else:
                return redirect('home')
    else:
        form = form_class(initial=questionnaire_answers)

    already_filled = questionnaire.is_filled_by(user)

    return render(request, 'questionnaire/questionnaire.html', {
        'questionnaire': questionnaire,
        # Need for dict() because a bug: https://code.djangoproject.com/ticket/16335
        'variant_checked_show_conditions': dict(
            questionnaire.variant_checked_show_conditions
        ),
        'form': form,
        'typing_dynamics_form': typing_dynamics_form,
        'already_filled': already_filled,
        'is_closed': is_closed,
    })


@login_required
def questionnaire(request, questionnaire_name):
    return questionnaire_for_user(request, request.user, questionnaire_name)


@login_required
def reset(request, questionnaire_name):
    questionnaire = get_object_or_404(models.Questionnaire,
                                      school__isnull=True,
                                      short_name=questionnaire_name)

    models.QuestionnaireAnswer.objects.filter(
        user=request.user,
        questionnaire=questionnaire
    ).delete()
    models.UserQuestionnaireStatus.objects.update_or_create(
        questionnaire=questionnaire,
        user=request.user,
        defaults={
            'status': models.UserQuestionnaireStatus.Status.NOT_FILLED
        },
    )

    return redirect(questionnaire)
