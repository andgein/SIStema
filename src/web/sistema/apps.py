from django.apps import AppConfig

from sistema.markdown_mailto_links import enable_mailto_links_in_markdown


class SistemaConfig(AppConfig):
    name = 'sistema'
    verbose_name = 'Sistema'

    def ready(self):
        enable_mailto_links_in_markdown()
