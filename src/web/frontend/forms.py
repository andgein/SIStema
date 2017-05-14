import copy

from dal.widgets import QuerySetSelectMixin

from django import forms
from django.core.exceptions import ValidationError
from django.forms import widgets
from django.forms.forms import BoundField
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_text
from django.utils.html import format_html

# TODO: move to the frontend application
from django.utils.safestring import mark_safe


class SistemaTextInput(forms.TextInput):
    def __init__(self, fa=None, **kwargs):
        super().__init__(**kwargs)
        self.fa_type = fa

    @property
    def fa_type_safe(self):
        return self.fa_type.replace(r'"', r'\"')

    def render(self, name, value, attrs=None):
        attrs = copy.deepcopy(attrs) or {}
        attrs['class'] = attrs.get('class', '') + ' gui-input'

        base_rendered = super().render(name, value, attrs=attrs)

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

    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs)
        attrs['class'] = attrs.get('class', '') + ' gui-textarea'

        base_rendered = super().render(name, value, attrs=attrs)

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
    def render(self, name, value, attrs=None):
        attrs = copy.deepcopy(attrs) or {}
        attrs['class'] = attrs.get('class', '') + ' gui-input'

        base_rendered = super().render(name, value, attrs=attrs)

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

    def render(self, name, value, attrs=None):
        base_rendered = super().render(name, value, attrs=attrs)

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

    def render(self, name, value, attrs=None):
        base_rendered = super().render(name, value, attrs=attrs)

        return '<label class="field prepend-icon">%s<label class="field-icon"><i class="fa fa-%s"></i></label>' % \
               (base_rendered, self.fa_type_safe)


class SistemaChoiceInput(widgets.ChoiceInput):
    def render(self, name=None, value=None, attrs=None, choices=()):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs

        block_or_online = 'inline' if 'inline' in attrs and attrs['inline'] else 'block'
        label_classes = [block_or_online]

        if 'disabled' in attrs and attrs['disabled']:
            label_classes.append('option-disabled')
        else:
            label_classes.append('option-alert')

        return format_html(
            '<label{} class="option {} mt5">{} <span class="{}"></span> {}</label>',
            label_for,
            ' '.join(label_classes),
            self.tag(attrs),
            self.input_type,
            self.choice_label
        )


# TODO: it's not working and not used now
class ButtonGroup(widgets.NumberInput):
    def render(self, name, value, attrs=None):
        """
            <div class="btn-toolbar inline">
                <div class="btn-group inline" data-toggle="buttons-radio">
                    <a class="btn inline active" onClick="$('#theory_2').val('0')">0</a>
                    <a class="btn inline" onClick="$('#theory_2').val('1')">1</a>
                    <a class="btn inline" onClick="$('#theory_2').val('2')">2</a>
                    <a class="btn inline" onClick="$('#theory_2').val('3')">3</a>
                    <a class="btn inline" onClick="$('#theory_2').val('4')">4</a>
                    <a class="btn inline" onClick="$('#theory_2').val('5')">5</a>
                </div>
            </div>
        """
        hidden_input = widgets.HiddenInput().render(name, value, attrs)

        return format('''
        <div class="btn-toolbar inline">
            <div class="btn-group inline" data-toggle="buttons-radio">
                <a class="btn inline" onClick="$('#theory_2').val('4')">4</a>
                <a class="btn inline" onClick="$('#theory_2').val('5')">5</a>
            </div>
        </div>
        ''')


class SistemaRadioChoiceInput(SistemaChoiceInput, widgets.RadioChoiceInput):
    input_type = 'radio'


class SistemaCheckboxChoiceInput(SistemaChoiceInput, widgets.CheckboxChoiceInput):
    input_type = 'checkbox'


class SistemaChoiceFieldRendererWithDisabled(widgets.ChoiceFieldRenderer):
    outer_html = '{content}'
    inner_html = '{choice_value}'

    def render(self):
        """
        To disable an option, pass a dict instead of a string for its label,
        of the form: {'label': 'option label', 'disabled': True}

        Based on django.forms.widgets.ChoiceFieldRenderer.render()
        """
        id_ = self.attrs.get('id')
        output = []

        for i, choice in enumerate(self.choices):
            item_attrs = self.attrs.copy()
            choice_value, choice_label = choice
            if isinstance(choice_label, dict):
                if 'disabled' in choice_label and choice_label['disabled']:
                    item_attrs['disabled'] = choice_label['disabled']
                choice_label = choice_label['label']

            w = self.choice_input_class(self.name, self.value,
                                        item_attrs, (choice_value, choice_label), i)
            output.append(format_html(self.inner_html,
                                      choice_value=force_text(w), sub_widgets=''))
        return format_html(self.outer_html,
                           id_attr=format_html(' id="{}"', id_) if id_ else '',
                           content=mark_safe('\n'.join(output)))


class SistemaRadioFieldRenderer(SistemaChoiceFieldRendererWithDisabled):
    choice_input_class = SistemaRadioChoiceInput


class SistemaCheckboxFieldRenderer(SistemaChoiceFieldRendererWithDisabled):
    choice_input_class = SistemaCheckboxChoiceInput


class SistemaRadioSelect(forms.RadioSelect):
    renderer = SistemaRadioFieldRenderer


class SistemaCheckboxSelect(forms.CheckboxSelectMultiple):
    renderer = SistemaCheckboxFieldRenderer


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
            file_size = file._size
            if file_size > self.max_upload_size:
                raise ValidationError('Размер файла (%s) превышет допустимый (%s)' % (
                    filesizeformat(file_size), filesizeformat(self.max_upload_size)))

        return data


class AutocompleteSelect2WidgetMixin(object):
    """Mixin for Select2 widgets.

    This class has been copied from dal_select2/widgets.py,
    but we replaced select2's files with our analogies.
    """

    class Media:
        """Automatically include static files for the admin."""

        css = {
            'all': (
                'vendor/plugins/select2/css/core.css',
                'vendor/plugins/select2/css/theme/default/layout.css',
            )
        }
        js = (
            'autocomplete_light/jquery.init.js',
            'autocomplete_light/autocomplete.init.js',
            'vendor/plugins/select2/select2.full.min.js',
            'autocomplete_light/forward.js',
            'autocomplete_light/select2.js',
        )

    autocomplete_function = 'select2'


class ModelAutocompleteSelect2(QuerySetSelectMixin,
                               AutocompleteSelect2WidgetMixin,
                               forms.Select):
    """Select widget for QuerySet choices and Select2."""


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


BoundField.label_tag = add_classes_to_label(BoundField.label_tag, 'control-label')
widgets.Input.render = add_classes_to_label(widgets.Input.render, 'form-control')
widgets.Select.render = add_classes_to_label(widgets.Select.render, 'form-control')


