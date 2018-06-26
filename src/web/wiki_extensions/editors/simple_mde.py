from django import forms

import wiki.editors.base


class SimpleMDEWidget(forms.Widget):
    template_name = "wiki_extensions/forms/simplemde.html"

    def __init__(self, attrs=None):
        # The 'rows' and 'cols' attributes are required for HTML correctness.
        default_attrs = {
            'class': 'simple-mde',
            'rows': '10',
            'cols': '40',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class SimpleMDE(wiki.editors.base.BaseEditor):
    editor_id = 'simplemde'

    def get_admin_widget(self, instance=None):
        return SimpleMDEWidget()

    def get_widget(self, instance=None):
        return SimpleMDEWidget()

    class AdminMedia:
        css = {
            'all': (
                "wiki_extensions/simplemde/simplemde.min.css",
                "wiki_extensions/simplemde/simplemde.wiki.css",
            )
        }
        js = (
            "wiki_extensions/simplemde/simplemde.min.js",
            "wiki_extensions/simplemde/simplemde.wiki.init.js",
        )

    class Media:
        css = {
            'all': (
                "wiki_extensions/simplemde/simplemde.min.css",
                "wiki_extensions/simplemde/simplemde.wiki.css",
            )
        }
        js = (
            "wiki_extensions/simplemde/simplemde.min.js",
            "wiki_extensions/simplemde/simplemde.wiki.init.js",
        )
