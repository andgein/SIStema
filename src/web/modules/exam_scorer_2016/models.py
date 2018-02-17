from django.db import models

import modules.entrance.models as entrance_models


class EntranceExamScorer(models.Model):
    name = models.CharField(max_length=100)

    max_level = models.ForeignKey(
        entrance_models.EntranceLevel,
        on_delete=models.CASCADE,
        related_name='+',
    )

    def __str__(self):
        return 'Scorer {}'.format(self.name)

    def get_score(self, school, user, user_tasks):
        test_tasks = list(
            filter(lambda t: hasattr(t, 'testentranceexamtask'), user_tasks))
        program_tasks = list(
            filter(lambda t: hasattr(t, 'programentranceexamtask'), user_tasks))
        return (self.get_test_score(user, test_tasks) +
                self.get_practice_score(user, program_tasks))

    def get_test_score(self, user, tasks):
        test_scores = list(TestCountScore.objects.filter(scorer=self))
        score_by_count = {test_score.count: test_score.score
                          for test_score in test_scores}

        count = sum(1 for task in tasks if task.is_last_correct)

        return score_by_count.get(count, 0)

    def get_practice_score(self, user, tasks):
        p_scores = list(ProgramTaskScore.objects.filter(scorer=self).order_by('score'))
        max_score = {p_score.task.id: p_score.score for p_score in p_scores}
        score = {p_score.task.id: 0 for p_score in p_scores}

        # First assign score for solved problems for this parallel
        for task in tasks:
            if task.is_solved and task.id in score:
                score[task.id] = max_score[task.id]

        # Then make harder solved problems replace the most valuble not scored
        # problems for this parallel
        harder_task_ids = set()
        harder_levels = entrance_models.EntranceLevel.objects.filter(order__gt=self.max_level.order)
        for level in harder_levels:
            for task in level.tasks.all():
                if task in tasks and task.id not in score:
                    harder_task_ids.add(task.id)

        for task in tasks:
            if task.id in harder_task_ids and task.is_solved:
                max_id, max_sc = None, 0
                for t_id in score:
                    if score[t_id] == 0 and max_score[t_id] > max_sc:
                        max_id, max_sc = t_id, max_score[t_id]
                if max_id:
                    score[max_id] = max_sc

        return sum(score.values())


class ProgramTaskScore(models.Model):
    scorer = models.ForeignKey(
        EntranceExamScorer,
        on_delete=models.CASCADE,
    )

    task = models.ForeignKey(
        entrance_models.ProgramEntranceExamTask,
        on_delete=models.CASCADE,
        related_name='+',
    )

    score = models.IntegerField()

    def __str__(self):
        return 'ProgramTaskScore({}, {}, {})'.format(self.scorer, self.task,
                                                     self.score)


class TestCountScore(models.Model):
    scorer = models.ForeignKey(
        EntranceExamScorer,
        on_delete = models.CASCADE,
    )

    count = models.IntegerField()

    score = models.IntegerField()

    def __str__(self):
        return 'TestCountScore({}, {}, {})'.format(self.scorer, self.count,
                                                   self.score)
