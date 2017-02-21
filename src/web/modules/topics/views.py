from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.db import transaction
from django.http.response import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect

from . import models
from . import issuer
from . import mark_guesser


class TopicWithUserMarks:
    def __init__(self, topic):
        self.topic = topic
        self._marks = []

    def add_mark(self, mark):
        self._marks.append(mark)

    @property
    def exists_automatically_mark(self):
        return any(mark.is_automatically for mark in self._marks)

    @property
    def all_marks_are_automatically(self):
        return all(mark.is_automatically for mark in self._marks)

    @property
    def marks(self):
        return sorted(self._marks, key=lambda mark: mark.scale_in_topic.scale_label_group.scale.short_name)


def topic_questionnaire_view(view):
    def func_wrapper(request, *args, **kwargs):
        if request.school is None:
            return HttpResponseNotFound()

        request.questionnaire = get_object_or_404(models.TopicQuestionnaire, school=request.school)
        return view(request, *args, **kwargs)

    func_wrapper.__name__ = view.__name__
    func_wrapper.__doc__ = view.__doc__
    func_wrapper.__module__ = view.__module__
    return func_wrapper


def _update_questionnaire_status(user, questionnaire, status):
    user_status, _ = models.UserQuestionnaireStatus.objects.update_or_create(user=user,
                                                                             questionnaire=questionnaire,
                                                                             defaults={
                                                                                 'status': status
                                                                             })


# TODO: return user_status.status instead of user_status
def _get_questionnaire_status(user, questionnaire):
    # Get user status or initialize it as NOT_STARTED
    user_status, _ = models.UserQuestionnaireStatus.objects.get_or_create(
            questionnaire=questionnaire,
            user=user,
            defaults={'status': models.UserQuestionnaireStatus.Status.NOT_STARTED})

    return user_status


def _get_user_marks_by_topics(user, questionnaire, not_show_auto_marks=True):
    """
    :return: Возвращает все оценки пользователя, сгруппированные по темам, в виде массива объектов TopicWithUserMarks
    """
    user_marks = models.UserMark.objects.filter(user=user,
                                                scale_in_topic__topic__questionnaire=questionnaire) \
        .prefetch_related('scale_in_topic__topic') \
        .prefetch_related('scale_in_topic__scale_label_group__scale')

    # Only staff can see automatically marks
    if not_show_auto_marks and not user.is_staff:
        user_marks = user_marks.filter(is_automatically=False)

    # Grouping marks for the same topics
    topics_with_marks = {}
    for mark in user_marks:
        mark_topic = mark.scale_in_topic.topic
        topic_with_marks = topics_with_marks.get(mark_topic.id, TopicWithUserMarks(mark_topic))

        # TODO: Hell..
        mark.label = mark.scale_in_topic.scale_label_group.labels.filter(mark=mark.mark).get().label_text

        topic_with_marks.add_mark(mark)
        topics_with_marks[mark_topic.id] = topic_with_marks

    # Ignore keys in dict
    return topics_with_marks.values()


# TODO: copy-paste with correcting(request)
def show_final_answers(request, user):
    topics_with_marks = _get_user_marks_by_topics(user, request.questionnaire, not_show_auto_marks=False)
    topics_with_marks = sorted(topics_with_marks, key=lambda t: t.topic.order)

    return render(request, 'topics/answers.html', {
        'questionnaire': request.questionnaire,
        'topics': topics_with_marks,
    })


def correcting(request):
    topics_with_marks = _get_user_marks_by_topics(request.user, request.questionnaire, not_show_auto_marks=False)
    topics_with_marks = sorted(topics_with_marks, key=lambda t: t.topic.order)

    return render(request, 'topics/correcting.html', {
        'questionnaire': request.questionnaire,
        'topics': topics_with_marks,
    })


@login_required
@topic_questionnaire_view
@transaction.atomic
def correcting_topic_marks(request, topic_name):
    if request.questionnaire.is_closed():
        return redirect('school:topics:index', school_name=request.school.short_name)

    user_status = _get_questionnaire_status(request.user, request.questionnaire)
    if user_status.status != models.UserQuestionnaireStatus.Status.CORRECTING:
        return redirect('school:topics:index', school_name=request.school.short_name)

    topic = get_object_or_404(models.Topic, questionnaire=request.questionnaire, short_name=topic_name)

    topic_issuer = issuer.TopicIssuer(request.user, request.questionnaire)
    topic_issue = topic_issuer.reissue_topic(topic, topic.scaleintopic_set.all())

    topic_issue.is_correcting = True
    topic_issue.save()

    return _show_or_process_topic_form(request, topic_issue)


@transaction.atomic
def backup_user_marks(user, scale_in_topic):
    user_marks = models.UserMark.objects.filter(user=user, scale_in_topic=scale_in_topic)
    for mark in user_marks:
        models.BackupUserMark.objects.get_or_create(user=user,
                                                    scale_in_topic=scale_in_topic,
                                                    defaults={
                                                        'mark': mark.mark,
                                                        'is_automatically': mark.is_automatically,
                                                    })
    user_marks.delete()


def _show_or_process_topic_form(request, topic_issue):
    guesser = mark_guesser.MarkGuesser(request.user, request.questionnaire)
    form_class = topic_issue.topic.get_form_class(topic_issue.scales.all())

    user_status = _get_questionnaire_status(request.user, request.questionnaire)
    is_correcting = user_status.status == models.UserQuestionnaireStatus.Status.CORRECTING

    is_closed = request.questionnaire.is_closed()

    if request.method == 'POST':
        form = form_class(data=request.POST)

        # Clean form for creating form.cleaned_data
        form.full_clean()

        if is_closed:
            form.add_error(None, 'Вступительная работа завершена. Изменения в тематическую анкету больше не принимаются')

        # Check that topic_id from form is equal to last issued topic, else update page for show the new question
        if 'topic_id' in form.cleaned_data and form.cleaned_data['topic_id'] != topic_issue.topic_id:
            return redirect('.')

        if form.is_valid():
            # For each scale in topic get mark from POST and save it as UserMark
            for field_name, field_value in form.cleaned_data.items():
                if field_name == 'topic_id':
                    continue

                # TODO: Deny to have '__' in Scale.short_name and ScaleLabelGroup.short_name?
                topic_name, scale_name, label_group_name = field_name.split('__', 3)
                scale_in_topic = models.ScaleInTopic.objects.filter(topic_id=topic_issue.topic_id,
                                                                    scale_label_group__scale__short_name=scale_name,
                                                                    scale_label_group__short_name=label_group_name).get()

                # Backup previous marks if user correcting their
                if is_correcting:
                    backup_user_marks(request.user, scale_in_topic)

                user_mark = models.UserMark(user=request.user,
                                            scale_in_topic=scale_in_topic,
                                            mark=field_value)
                user_mark.save()

            # Guess some marks automatically
            guesser.update_automatically_marks()

            # Issue new topic for user
            topic_issuer = issuer.TopicIssuer(request.user, request.questionnaire)
            no_more_topics = not topic_issuer.find_and_issue_new_topic_for_user()
            if no_more_topics:
                _update_questionnaire_status(request.user, request.questionnaire,
                                             models.UserQuestionnaireStatus.Status.CORRECTING)

            # ... and redirect to view the new question
            return redirect('school:topics:index', school_name=request.school.short_name)

    else:
        form = form_class()

    # Order marks by created time descending
    marks = sorted(_get_user_marks_by_topics(request.user, request.questionnaire),
                   key=lambda t: min(t._marks, key=lambda m: m.created_at).created_at,
                   reverse=True)

    return render(request, 'topics/question.html', {'questionnaire': request.questionnaire,
                                                    'topic': topic_issue.topic,
                                                    'form': form,
                                                    'issued_topics': marks,
                                                    'is_correcting': is_correcting})


@login_required
@topic_questionnaire_view
@transaction.atomic
def index(request):
    user_status = _get_questionnaire_status(request.user, request.questionnaire)

    # Disable access for users which already filled an questionnaire
    if user_status.status == models.UserQuestionnaireStatus.Status.FINISHED:
        return show_final_answers(request, request.user)

    topic_issuer = issuer.TopicIssuer(request.user, request.questionnaire)

    if request.method == 'GET':
        # Show correcting form if need
        if user_status.status == models.UserQuestionnaireStatus.Status.CORRECTING:
            return correcting(request)

        # If user has not filled a questionnaire et all
        if user_status.status == models.UserQuestionnaireStatus.Status.NOT_STARTED:
            # Update his status, mark it as STARTED
            user_status.status = models.UserQuestionnaireStatus.Status.STARTED
            user_status.save()

            # ... and issue first topic
            no_more_topics = not topic_issuer.find_and_issue_new_topic_for_user()
            if no_more_topics:
                _update_questionnaire_status(request.user, request.questionnaire,
                                             models.UserQuestionnaireStatus.Status.CORRECTING)
                return redirect('.')

    topic_issue = topic_issuer.get_last_issued_topic()

    return _show_or_process_topic_form(request, topic_issue)


@login_required
@topic_questionnaire_view
def reset(request):
    models.UserQuestionnaireStatus.objects.filter(user=request.user,
                                                  questionnaire=request.questionnaire).delete()
    models.TopicIssue.objects.filter(user=request.user,
                                     topic__questionnaire=request.questionnaire).delete()
    models.UserMark.objects.filter(user=request.user,
                                   scale_in_topic__topic__questionnaire=request.questionnaire).delete()
    models.BackupUserMark.objects.filter(user=request.user,
                                         scale_in_topic__topic__questionnaire=request.questionnaire).delete()
    _update_questionnaire_status(request.user, request.questionnaire, models.UserQuestionnaireStatus.Status.NOT_STARTED)

    return redirect('school:topics:index', school_name=request.school.short_name)


@login_required
@topic_questionnaire_view
def finish(request):
    _update_questionnaire_status(request.user, request.questionnaire, models.UserQuestionnaireStatus.Status.FINISHED)

    return redirect(request.school)
