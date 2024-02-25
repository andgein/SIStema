import copy

from dal.widgets import QuerySetSelectMixin

from django import forms
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat


class SistemaTextInput(forms.TextInput):
    def __init__(self, fa=None, **kwargs):
        super().__init__(**kwargs)
        self.fa_type = fa

    @property
    def fa_type_safe(self):
        return self.fa_type.replace(r'"', r'\"')

    def render(self, name, value, attrs=None, renderer=None):
        attrs = copy.deepcopy(attrs) or {}
        attrs['class'] = attrs.get('class', '') + ' gui-input'

        base_rendered = super().render(name, value, attrs=attrs, renderer=renderer)

        icon_html = ('<label class="field-icon"><i class="fa fa-{}"></i>'
                     '</label>'.format(self.fa_type) if self.fa_type else '')

        label_classes = ['field']
        if self.fa_type:
            label_classes.append('prepend-icon')

        return ('<label class="{label_classes}">{base_rendered}{icon_html}'
                '</label>'.format(
                    label_classes=' '.join(label_classes),
                    base_rendered=base_rendered,
                    icon_html=icon_html))


# TODO(Artem Tabolin): this class duplicates the class above in everything
#     except the base class. Can we avoid that? Maybe make some kind of mixin?
class SistemaTextarea(forms.Textarea):
    def __init__(self, fa=None, **kwargs):
        super().__init__(**kwargs)
        self.fa_type = fa

    @property
    def fa_type_safe(self):
        return self.fa_type.replace(r'"', r'\"')

    def render(self, name, value, attrs=None, renderer=None):
        attrs = self.build_attrs(attrs)
        attrs['class'] = attrs.get('class', '') + ' gui-textarea'

        base_rendered = super().render(name, value, attrs=attrs, renderer=renderer)

        icon_html = ('<label class="field-icon"><i class="fa fa-{}"></i>'
                     '</label>'.format(self.fa_type) if self.fa_type else '')

        label_classes = ['field']
        if self.fa_type:
            label_classes.append('prepend-icon')

        return ('<label class="{label_classes}">{base_rendered}{icon_html}'
                '</label>'.format(
                    label_classes=' '.join(label_classes),
                    base_rendered=base_rendered,
                    icon_html=icon_html))


class SistemaNumberInput(forms.NumberInput):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = copy.deepcopy(attrs) or {}
        attrs['class'] = attrs.get('class', '') + ' gui-input'

        base_rendered = super().render(name, value, attrs=attrs, renderer=renderer)

        return '<label class="field">{}</label>'.format(base_rendered)


# TODO(Artem Tabolin): migrate all the usages to SistemaTextInput and remove
class TextInputWithFaIcon(forms.TextInput):
    fa_type = None

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is not None:
            self.fa_type = attrs.pop('fa', self.fa_type)

    @property
    def fa_type_safe(self):
        return self.fa_type.replace(r'"', r'\"')

    def render(self, name, value, attrs=None, renderer=None):
        base_rendered = super().render(name, value, attrs=attrs, renderer=renderer)

        return '<label class="field prepend-icon">%s<label class="field-icon"><i class="fa fa-%s"></i></label>' % \
               (base_rendered, self.fa_type_safe)


class PasswordInputWithFaIcon(forms.PasswordInput, TextInputWithFaIcon):
    pass


# TODO(Artem Tabolin): migrate all the usages to SistemaTextarea and remove
class TextareaWithFaIcon(forms.Textarea):
    fa_type = None

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is not None:
            self.fa_type = attrs.pop('fa', self.fa_type)

    @property
    def fa_type_safe(self):
        return self.fa_type.replace(r'"', r'\"')

    def render(self, name, value, attrs=None, renderer=None):
        base_rendered = super().render(name, value, attrs=attrs, renderer=renderer)

        return '<label class="field prepend-icon">%s<label class="field-icon"><i class="fa fa-%s"></i></label>' % \
               (base_rendered, self.fa_type_safe)


class SistemaRadioSelect(forms.RadioSelect):
    template_name = 'frontend/forms/widgets/radio.html'
    option_template_name = 'frontend/forms/widgets/radio_option.html'


class SistemaCheckboxSelect(forms.CheckboxSelectMultiple):
    template_name = 'frontend/forms/widgets/checkbox_select.html'
    option_template_name = 'frontend/forms/widgets/checkbox_option.html'


class RestrictedFileField(forms.FileField):
    """
    Same as FileField, but you can specify:
    * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
    * max_upload_size - a number indicating the maximum file size allowed for upload (in bytes).
    """

    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop('content_types', None)
        self.max_upload_size = kwargs.pop('max_upload_size', None)

        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        file = super().clean(data, initial)

        if self.content_types is not None:
            content_type = file.content_type
            if content_type not in self.content_types:
                raise ValidationError('Файл неверного формата')

        if self.max_upload_size is not None:
            file_size = file.size
            if file_size > self.max_upload_size:
                raise ValidationError('Размер файла (%s) превышет допустимый (%s)' % (
                    filesizeformat(file_size), filesizeformat(self.max_upload_size)))

        return data


class AutocompleteSelect2WidgetMixin(object):
    """Mixin for Select2 widgets.

    This class has been copied from Select2WidgetMixin from dal_select2/widgets.py,
    but we replaced select2's files with our analogies.
    """

    class Media:
        """Automatically include static files for the admin."""

        css = {
            'all': (
                'vendor/plugins/select2/css/core.css',
                'vendor/plugins/select2/css/theme/default/layout.css',
                'admin/css/autocomplete.css',
                'autocomplete_light/select2.css',
            )
        }
        js = (
            'vendor/plugins/select2/select2.full.min.js',
            'autocomplete_light/autocomplete_light.js',
            'autocomplete_light/select2.js',
        )

    autocomplete_function = 'select2'


class ModelAutocompleteSelect2(QuerySetSelectMixin,
                               AutocompleteSelect2WidgetMixin,
                               forms.Select):
    """Select widget for QuerySet choices and Select2."""


class ModelAutocompleteMultipleSelect2(QuerySetSelectMixin,
                                       AutocompleteSelect2WidgetMixin,
                                       forms.SelectMultiple):
    """Multiple select widget for QuerySet choices and Select2."""


class SelectWithDisabledOptions(forms.Select):
    """
    Subclass of Django's select widget that allows disabling options.
    See https://www.djangosnippets.org/snippets/10646/
    """

    def __init__(self, *args, **kwargs):
        self._disabled_choices = kwargs.pop('disabled_choices', [])
        super().__init__(*args, **kwargs)

    @property
    def disabled_choices(self):
        return self._disabled_choices

    @disabled_choices.setter
    def disabled_choices(self, other):
        self._disabled_choices = other

    def create_option(self, name, value, *args, **kwargs):
        option_dict = super().create_option(name, value, *args, **kwargs)
        if value in self.disabled_choices:
            option_dict['attrs']['disabled'] = 'disabled'
        return option_dict


def add_classes_to_label(f, classes=''):
    def func_wrapper(self, *args, **kwargs):
        if hasattr(self, 'attrs'):
            exists_classes = self.attrs.get('class', '')
            if '-' + classes not in exists_classes.split():
                self.attrs['class'] = exists_classes + ' ' + classes
        else:
            # TODO: bug? What if kwargs['attrs'] is not defined?
            if 'attrs' in kwargs:
                attrs = kwargs.pop('attrs', {})
                attrs['class'] = attrs.get('class', '') + ' ' + classes
                kwargs['attrs'] = attrs
        return f(self, *args, **kwargs)

    func_wrapper.__name__ = f.__name__
    func_wrapper.__module__ = f.__module__
    func_wrapper.__doc__ = f.__doc__
    return func_wrapper


forms.BoundField.label_tag = add_classes_to_label(
    forms.BoundField.label_tag,
    'control-label',
)
# TODO(artemtab): Space at the end of the CSS class is a workaround for
#     https://code.djangoproject.com/ticket/29221. We can remove it as soon as
#     we upgrade to Django 2.0.4
# TODO: Input is private for django, refactor not to reference it
forms.widgets.Input.render = add_classes_to_label(forms.widgets.Input.render, 'form-control ')
forms.Select.render = add_classes_to_label(forms.Select.render, 'form-control ')
