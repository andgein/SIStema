from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PolygonWikiExtensionsConfig(AppConfig):
    name = 'modules.polygon.wiki'
    verbose_name = _("Polygon extensions for SIStema wiki")
    label = 'polygon_sistema_wiki'
