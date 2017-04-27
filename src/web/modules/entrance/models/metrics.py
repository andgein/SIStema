import collections
import itertools

from django.core.cache import cache
from django.db import models, IntegrityError
from django.utils.functional import cached_property

import polymorphic.models

import modules.ejudge.models
import users.models as users_models

from . import checking as checking_models
from . import main as main_models


class EntranceUserMetric(polymorphic.models.PolymorphicModel):
    """
    Some metric to show for enrolling users.
    """
    name = models.CharField(max_length=100)

    exam = models.ForeignKey(
        main_models.EntranceExam,
        on_delete=models.CASCADE,
        related_name='metrics',
    )

    # Should the metric be cached? Use for heavy metrics
    CACHE = False

    # Cache timeout for the metric in seconds
    TIMEOUT = 300

    class Meta:
        unique_together = ('name', 'exam')

    def __str__(self):
        return 'Метрика {} для {}'.format(self.name, self.exam)

    @cached_property
    def cache_key(self):
        local_key = '-'.join(str(x) for x in (self.pk, self.exam.pk))
        return 'entrance.EntranceUserMetric-' + local_key

    def values_for_users(self, users):
        """
        Return a list of metric values for given users.

        This method contains only the caching logic. Actual metric retrieval is
        done in values_for_users_internal method.
        """
        if not self.CACHE:
            return self._values_for_users(users)

        cached_value_by_user_id = cache.get(self.cache_key)
        if cached_value_by_user_id is None:
            users_to_cache = (
                users_models.User.objects
                .filter(entrance_statuses__school=self.exam.school)
                .exclude(entrance_statuses__status=
                         main_models.EntranceStatus.Status.NOT_PARTICIPATED)
            )
            cached_value_by_user_id = {
                user.id: value
                for user, value in zip(users_to_cache,
                                       self._values_for_users(users_to_cache))
            }
            cache.set(
                self.cache_key, cached_value_by_user_id, timeout=self.TIMEOUT)

        values = []
        missing_users = []
        missing_indices = []
        for i, user in enumerate(users):
            cached_value = cached_value_by_user_id.get(user.id, None)
            values.append(cached_value)
            if cached_value is None:
                missing_users.append(user)
                missing_indices.append(i)

        if missing_users:
            missing_values = self._values_for_users(missing_users)
            for i, value in zip(missing_indices, missing_values):
                values[i] = value

        return values

    def _values_for_users(self, users):
        """
        Return a list of metric values for given users. Should be implemented by
        descendants.
        """
        raise NotImplementedError()

    def value_for_user(self, user):
        """
        Return metric value for the specified user
        """
        return self.values_for_users([user])[0]

    def annotate_users(self, users, field_name):
        """
        Assign metric value for each user to the attribute named field_name
        """
        for user, value in zip(users, self.values_for_users(users)):
            setattr(user, field_name, value)


# I've implemented just a single uber-metric for efficency reason as we don't
# now have much time to carefully design and optimize. Eventually we may want to
# have a more flexible way to compute parallel score and different miscellaneous
# metrics such as number of the solved theoretical tasks in a given group for
# example.
class ParallelScoreEntranceUserMetric(EntranceUserMetric):
    """
    Total weighted score for several program tasks. Each unsolved task can be
    replaced by any task from replacing_program_tasks set.
    """
    CACHE = True

    # TODO(artemtab): find a way to restrict these task to belong to the same
    #     exam as the metric itself.
    replacing_program_tasks = models.ManyToManyField(
        main_models.ProgramEntranceExamTask,
        related_name='+',
    )

    max_theory_score = models.IntegerField(blank=True, null=True)

    def _values_for_users(self, users):
        # Theory
        file_task_ids = self.file_task_entries.values_list('task__id',
                                                           flat=True)
        checked_solutions = (
            checking_models.CheckedSolution.objects
            .filter(solution__user__in=users,
                    solution__task__id__in=file_task_ids)
            .order_by('created_at')
            .select_related('solution__user')
        )
        # If there are duplicate keys in dictionary comprehensions the last
        # always wins. That way we will use the score from the last available
        # check.
        last_score_by_user_and_task = {
            (checked_solution.solution.user.id,
             checked_solution.solution.task.id): checked_solution.score
            for checked_solution in checked_solutions
        }

        # Practice
        OK = modules.ejudge.models.CheckingResult.Result.OK
        replacing_task_ids = set(
            self.replacing_program_tasks.values_list('id', flat=True))
        main_task_ids = set(
            self.program_task_entries.values_list('task__id', flat=True))
        task_ids = itertools.chain(replacing_task_ids, main_task_ids)
        ok_solutions = set(
            main_models.ProgramEntranceExamTaskSolution.objects
            .filter(user__in=users,
                    task__id__in=task_ids,
                    ejudge_queue_element__submission__result__result=OK)
            .values_list('user__id', 'task__id')
        )

        replaces_count = collections.defaultdict(int)
        for user_id, task_id in ok_solutions:
            if task_id in replacing_task_ids:
                replaces_count[user_id] += 1

        # Total
        program_task_entries = self.program_task_entries.order_by('-score')
        file_task_entries = self.file_task_entries.all()
        for user in users:
            # Theory
            theory_score = sum(
                (last_score_by_user_and_task.get((user.id, entry.task.id), 0) /
                 entry.task.max_score * entry.max_score)
                for entry in file_task_entries
            )
            if self.max_theory_score is not None:
                theory_score = min(theory_score, self.max_theory_score)

            # Practice
            replaces_left = replaces_count[user.id]
            practice_score = 0
            for entry in program_task_entries:
                if (user.id, entry.task.id) in ok_solutions:
                    practice_score += entry.score
                elif replaces_left > 0:
                    replaces_left -= 1
                    practice_score += entry.score

            yield round(theory_score + practice_score)


class ParallelScoreEntranceUserMetricFileTaskEntry(models.Model):
    parallel_score_metric = models.ForeignKey(
        ParallelScoreEntranceUserMetric,
        on_delete=models.CASCADE,
        related_name='file_task_entries',
    )

    task = models.ForeignKey(
        main_models.FileEntranceExamTask,
        on_delete=models.CASCADE,
        related_name='+',
    )

    max_score = models.IntegerField()

    def save(self, *args, **kwargs):
        if self.task.exam != self.parallel_score_metric.exam:
            raise IntegrityError()
        super().save(*args, **kwargs)


class ParallelScoreEntranceUserMetricProgramTaskEntry(models.Model):
    parallel_score_metric = models.ForeignKey(
        ParallelScoreEntranceUserMetric,
        on_delete=models.CASCADE,
        related_name='program_task_entries',
    )

    task = models.ForeignKey(
        main_models.ProgramEntranceExamTask,
        on_delete=models.CASCADE,
        related_name='+',
    )

    score = models.IntegerField()

    def save(self, *args, **kwargs):
        if self.task.exam != self.parallel_score_metric.exam:
            raise IntegrityError()
        super().save(*args, **kwargs)
