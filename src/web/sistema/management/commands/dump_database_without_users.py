from django.apps import apps
from django.core import management
from django.db import models

from users.models import User


class Command(management.base.BaseCommand):
    help = 'Dump database to fixture without users and all models references ' \
           'to them'

    requires_migrations_checks = True

    @staticmethod
    def get_model_relations(model):
        return [
            f for f in model._meta.get_fields(include_hidden=True)
            # Sometimes we may need to include M2M fields in this list.
            # In this case add "or f.many_to_many"
            if (f.one_to_many or f.one_to_one) and f.auto_created and
               not f.concrete
        ]

    def get_related_models(self, model):
        relations = self.get_model_relations(model)
        # TODO (andgein): Find relations with on_delete=models.PROTECT
        # and do something with it?
        relations = [f for f in relations if f.on_delete is (models.CASCADE, models.SET_NULL)]
        return [field.related_model for field in relations]

    def get_models_references_to_model(self, model):
        processed_models = {model}
        models_to_process = [model]
        while models_to_process:
            current_model = models_to_process.pop()
            related_models = self.get_related_models(current_model)

            for related_model in related_models:
                if related_model not in processed_models:
                    models_to_process.append(related_model)
                    processed_models.add(related_model)

        return processed_models

    def handle(self, *args, **options):
        related_models = self.get_models_references_to_model(User)
        model_names = [
            model._meta.app_label + '.' + model._meta.model_name
            for model in related_models
        ]
        options['exclude'] = model_names
        options['traceback'] = True
        options['use_natural_foreign_keys'] = True
        options['use_natural_primary_keys'] = True
        management.call_command(
            'dumpdata', **options
        )

