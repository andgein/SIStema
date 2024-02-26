from django.apps import AppConfig

from sistema.markdown_mailto_links import enable_mailto_links_in_markdown
from django_nyt.apps import DjangoNytConfig
from wiki.apps import WikiConfig
from wiki.plugins.attachments.apps import AttachmentsConfig


class SistemaConfig(AppConfig):
    name = 'sistema'
    verbose_name = 'Sistema'

    def ready(self):
        enable_mailto_links_in_markdown()


# We have to modify the AppConfig for some modules as they don't have migration for BigAutoField.
# See https://stackoverflow.com/questions/67006488/migrating-models-of-dependencies-when-changing-default-auto-field.
class ModifiedDjangoNytConfig(DjangoNytConfig):
    default_auto_field = 'django.db.models.AutoField'


class ModifiedWikiConfig(WikiConfig):
    default_auto_field = 'django.db.models.AutoField'


class ModifiedAttachmentsConfig(AttachmentsConfig):
    default_auto_field = 'django.db.models.AutoField'
