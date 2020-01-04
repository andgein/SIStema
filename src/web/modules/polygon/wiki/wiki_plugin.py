from django.utils.translation import gettext as _
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.macros import settings


class PolygonPlugin(BasePlugin):

    slug = 'polygon_contest_plugin'

    sidebar = {'headline': _('Polygon'),
               'icon_class': 'fa-product-hunt',
               'template': 'polygon/wiki/sidebar.html',
               'form_class': None,
               'get_form_kwargs': (lambda a: {})}

    markdown_extensions = [
        'modules.polygon.wiki.mdx.contest',
    ]


registry.register(PolygonPlugin)
