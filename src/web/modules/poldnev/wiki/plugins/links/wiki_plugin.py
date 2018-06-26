"""
This plugin provides UI for inserting links to poldnev.ru

Currently only person links are supported.
"""

from django.urls import path, reverse_lazy
from wiki.core.plugins import registry
import wiki.core.plugins.base
from wiki.plugins.links import settings
from wiki.plugins.links.mdx.djangowikilinks import WikiPathExtension
from wiki.plugins.links.mdx.urlize import makeExtension as urlize_makeExtension

from . import views


class LinksPlugin(wiki.core.plugins.base.BasePlugin):
    slug = 'poldnev-links'

    urlpatterns = {
        'article': [
            path('json/person-link-data/', views.PersonLinkData.as_view(),
                 name='poldnev_person_link_data'),
        ],
    }

    sidebar = {'headline': 'poldnev.ru',
               'icon_class': 'fa-user',
               'template': 'poldnev/wiki/plugins/links/sidebar.html',
               'form_class': None,
               'get_form_kwargs': (lambda a: {})}


registry.register(LinksPlugin)
