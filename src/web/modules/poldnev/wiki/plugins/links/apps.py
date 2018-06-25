from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LinksConfig(AppConfig):
    name = 'modules.poldnev.wiki.plugins.links'
    verbose_name = _("Poldnev links")
    label = 'poldnev_links'
