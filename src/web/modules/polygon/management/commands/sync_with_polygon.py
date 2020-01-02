import django.core.mail
from constance import config
from django.conf import settings
from django.core import management
from django.db import transaction
from django.utils import translation
from polygon_client import Polygon

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

        for i in range(RETRIES):
            try:
                self.sync()
                break
            except RuntimeError as e:
                print(e)
                pass
        else:
            message = 'Error when syncing with polygon:\n{}'.format(e)
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

        problems = p.problems_list()
        print('Found {} problems in Polygon'.format(len(problems)))
        for polygon_problem in problems:
            with transaction.atomic():
                self.update_problem(polygon_problem)
                print('.', end='', flush=True)
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
