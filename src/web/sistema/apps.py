from django.apps import AppConfig

from sistema.markdown_mailto_links import enable_mailto_links_in_markdown
from django_nyt.apps import DjangoNytConfig


class SistemaConfig(AppConfig):
    name = 'sistema'
    verbose_name = 'Sistema'

    def ready(self):
        enable_mailto_links_in_markdown()


class ModifiedDjangoNytConfig(DjangoNytConfig):
    """
    We have to modify the AppConfig for django-nyt as it doesn't have migration for BigAutoField.
    See https://stackoverflow.com/questions/67006488/migrating-models-of-dependencies-when-changing-default-auto-field.
    """
    default_auto_field = 'django.db.models.AutoField'
