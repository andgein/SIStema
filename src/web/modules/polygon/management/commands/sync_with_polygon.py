import django.core.mail
from constance import config
from django.conf import settings
from django.core import management
from django.db import transaction
from django.utils import translation
from polygon_client import Polygon, PolygonRequestFailedException

from modules.polygon import models

RETRIES = 3


class Command(management.base.BaseCommand):
    help = 'Update problems metadata from Polygon'

    requires_migrations_checks = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error = None

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        # TODO(artemtab): more granular retries. At least we shouldn't repeat
        # successful Polygon requests if something unrelated goes wrong.
        last_exception = None
        for i in range(RETRIES):
            try:
                self.sync()
                break
            except Exception as e:
                print(e)
                last_exception = e
        else:
            message = (
                'Error when syncing with polygon:\n{}'.format(last_exception))
            print(message)
            django.core.mail.mail_admins('Sync with Polygon failed', message)
            return

    def sync(self):
        """
        Try to sync local polygon information with the actual Polygon.

        Throws an exception if something goes wrong.
        """

        p = Polygon(
            api_url=config.SISTEMA_POLYGON_URL,
            api_key=config.SISTEMA_POLYGON_KEY,
            api_secret=config.SISTEMA_POLYGON_SECRET,
        )

        # Problems
        problems = p.problems_list()
        print('Found {} problems in Polygon. Syncing...'.format(len(problems)))
        for polygon_problem in problems:
            with transaction.atomic():
                self.update_problem(polygon_problem)
                print('.', end='', flush=True)
        print()

        # Contests
        print('Syncing contests')
        contest_id = 1
        current_gap = 0
        while True:
            try:
                problem_set = p.contest_problems(contest_id)
                # Found a contest in Polygon. Reset the gap size.
                current_gap = 0
                print('.', end='', flush=True)
            except PolygonRequestFailedException:
                print('_', end='', flush=True)
                # If at some point the specified number of contests in a row are
                # missing we consider that there are no more contests to sync.
                current_gap += 1
                if current_gap > config.SISTEMA_POLYGON_MAXIMUM_CONTEST_ID_GAP:
                    break
            with transaction.atomic():
                self.update_contest(contest_id, problem_set)
            contest_id += 1
        print()

    def update_problem(self, polygon_problem):
        local_problem = (
            models.Problem.objects
            .filter(polygon_id=polygon_problem.id)
            .prefetch_related('tags')
            .first())

        if local_problem is None:
            local_problem = models.Problem(
                polygon_id=polygon_problem.id,
            )

        prev_revision = local_problem.revision

        local_problem.revision = polygon_problem.revision
        local_problem.name = polygon_problem.name
        local_problem.owner = polygon_problem.owner
        local_problem.deleted = polygon_problem.deleted
        local_problem.latest_package = polygon_problem.latest_package

        if prev_revision is None or local_problem.revision > prev_revision:
            self.update_problem_info(local_problem, polygon_problem)

        local_problem.save()

    def update_problem_info(self, local_problem, polygon_problem):
        info = polygon_problem.info()
        local_problem.input_file = info.input_file
        local_problem.output_file = info.output_file
        local_problem.interactive = info.interactive
        local_problem.time_limit = info.time_limit
        local_problem.memory_limit = info.memory_limit

        local_problem.general_description = (
            polygon_problem.general_description())
        local_problem.general_tutorial = (
            polygon_problem.general_tutorial())

        polygon_tags = polygon_problem.tags()
        self.create_missing_tags(polygon_tags)
        local_problem.tags.set(polygon_tags)

    def create_missing_tags(self, tags):
        for tag in tags:
            models.Tag.objects.get_or_create(tag=tag)

    def update_contest(self, contest_id, problem_set):
        contest = (
            models.Contest.objects
                .filter(polygon_id=contest_id)
                .first())
        if contest is None:
            contest = models.Contest(polygon_id=contest_id)
        contest.save()
        # Remove problems deleted from contest
        (models.ProblemInContest.objects
         .filter(contest_id=contest_id)
         .exclude(problem_id__in=[problem.id
                                  for problem in problem_set.values()])
         .delete())
        # Add/update problems which were added or re-ordered
        for index, problem in problem_set.items():
            models.ProblemInContest.objects.update_or_create(
                contest_id=contest_id,
                problem_id=problem.id,
                defaults={'index': index},
            )
