from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from djchoices import choices


class TopicCheckingQuestionnaire(models.Model):
    class Status(choices.DjangoChoices):
        IN_PROGRESS = choices.ChoiceItem(1)
        REFUSED = choices.ChoiceItem(2)
        FAILED = choices.ChoiceItem(3)
        PASSED = choices.ChoiceItem(4)

    topic_questionnaire = models.ForeignKey(
        'TopicQuestionnaire',
        on_delete=models.CASCADE,
        related_name='+',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='+',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    checked_at = models.DateTimeField(blank=True, null=True, default=None)

    status = models.PositiveIntegerField(
        choices=Status.choices,
        validators=[Status.validator],
    )

    @classmethod
    def get_latest(cls, user, topic_questionnaire):
        try:
            smartq_q = (
                cls.objects
                .filter(user=user, topic_questionnaire=topic_questionnaire)
                .latest('created_at'))
            return smartq_q
        except cls.DoesNotExist:
            return None

    def errors_count(self):
        err_count = 0
        for q in self.questions.all():
            # I was counting ok_counts, but artemtab made me think in negative
            # way
            if (q.checker_result !=
                    TopicCheckingQuestionnaireQuestion.CheckerResult.OK):
                err_count += 1
        return err_count

    def has_check_failed(self):
        failed = TopicCheckingQuestionnaireQuestion.CheckerResult.CHECK_FAILED
        for q in self.questions.all():
            if q.checker_result == failed:
                return True
        return False

    def is_check_failed_expired(self):
        return (timezone.now() >= self.checked_at +
                timedelta(minutes=30))


class TopicCheckingQuestionnaireQuestion(models.Model):
    # Modify together with smartq
    class CheckerResult(choices.DjangoChoices):
        # TODO: no doubling the Checker result from smartq
        OK = choices.ChoiceItem(1)
        WRONG_ANSWER = choices.ChoiceItem(2)
        PRESENTATION_ERROR = choices.ChoiceItem(3)
        CHECK_FAILED = choices.ChoiceItem(4)

    questionnaire = models.ForeignKey(
        TopicCheckingQuestionnaire,
        on_delete=models.CASCADE,
        related_name='questions',
    )

    generated_question = models.ForeignKey(
        'smartq.GeneratedQuestion',
        on_delete=models.CASCADE,
        related_name='+',
    )

    topic_mapping = models.ForeignKey(
        'QuestionForTopic',
        on_delete=models.CASCADE,
        related_name='+',

    )

    checker_result = models.PositiveIntegerField(
        choices=CheckerResult.choices,
        validators=[CheckerResult.validator],
        blank=True,
        null=True,
        default=None)

    checker_message = models.CharField(
        max_length=2000, blank=True, null=True, default=None)


class QuestionForTopic(models.Model):
    scale_in_topic = models.ForeignKey(
        'ScaleInTopic',
        on_delete=models.CASCADE,
        related_name='smartq_mapping',
        help_text='Question is for this topic',
    )

    mark = models.PositiveIntegerField(
        help_text='Question will be asked is this mark is equal to user mark '
                  'for topic')

    smartq_question = models.ForeignKey(
        'smartq.Question',
        on_delete=models.CASCADE,
        related_name='topic_mapping',
        help_text='Base checking question without specified numbers',
    )

    group = models.IntegerField(
        blank=True, null=True, default=None,
        help_text='Same group indicates similar questions, e.g. bfs/dfs, and '
                  'only one of them is asked')

    def __str__(self):
        return '{} -> {}'.format((self.scale_in_topic, self.mark),
                                 self.smartq_question)

    def copy_to_questionnaire(self, to_questionnaire):
        return self.__class__.objects.create(
            scale_in_topic=self.scale_in_topic.get_clone_in_questionnaire(
                to_questionnaire),
            mark=self.mark,
            smartq_question=self.smartq_question,
            group=self.group,
        )


class TopicCheckingSettings(models.Model):
    questionnaire = models.ForeignKey(
        'TopicQuestionnaire',
        on_delete=models.CASCADE,
    )

    max_questions = models.PositiveIntegerField()

    @property
    def allowed_errors_map(self):
        # TODO: not hardcode
        return {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 2}

    def copy_to_questionnaire(self, to_questionnaire):
        return self.__class__.objects.create(
            questionnaire=to_questionnaire,
            max_questions=self.max_questions,
        )
