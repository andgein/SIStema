from django import forms
from django.forms import widgets

import frontend.forms
import modules.ejudge.models


class EntranceTaskForm(forms.Form):
    def __init__(self, task, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['solution'].widget.attrs['id'] = '%s_%d' % (self.task_type, task.id)


class TestEntranceTaskForm(EntranceTaskForm):
    task_type = 'test'

    solution = forms.CharField(max_length=100,
                               label='',
                               label_suffix='',
                               widget=forms.TextInput(),
                               )


class FileEntranceTaskForm(EntranceTaskForm):
    task_type = 'file'

    solution = frontend.forms.RestrictedFileField(
        max_upload_size=5 * 1024 * 1024,
        required=True,
        label='',
        label_suffix='',
        widget=widgets.ClearableFileInput(
            attrs={
                'class': 'file -form-control',
                'data-language': 'ru',
                'data-show-upload': 'false',
                'data-show-remove': 'false',
                'data-show-preview': 'false',
                'data-browse-on-zone-click': 'true',
            }
        )
    )


class ProgramEntranceTaskForm(EntranceTaskForm):
    task_type = 'program'

    language = forms.ModelChoiceField(
        queryset=modules.ejudge.models.ProgrammingLanguage.objects.all(),
        to_field_name='id',
        required=True,
        empty_label='Язык программирования',
        label='Язык программирования',
        label_suffix=''
    )

    solution = frontend.forms.RestrictedFileField(
        max_upload_size=64 * 1024,
        required=True,
        label='Выберите файл с программой',
        label_suffix='',
        widget=widgets.ClearableFileInput(
            attrs={
                'class': 'file -form-control',
                'data-language': 'ru',
                'data-show-upload': 'false',
                'data-show-remove': 'false',
                'data-show-preview': 'false',
                'data-browse-on-zone-click': 'true',
            }
        )
    )


class OutputOnlyEntranceTaskForm(EntranceTaskForm):
    task_type = 'output-only'

    solution = frontend.forms.RestrictedFileField(
        max_upload_size=512 * 1024,
        required=True,
        label='Выберите файл',
        label_suffix='',
        widget=widgets.ClearableFileInput(
            attrs={
                'class': 'file -form-control',
                'data-language': 'ru',
                'data-show-upload': 'false',
                'data-show-remove': 'false',
                'data-show-preview': 'false',
                'data-browse-on-zone-click': 'true',
            }
        )
    )


class SelectEnrollmentTypeForm(forms.Form):
    def __init__(self, enrollment_types, disabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for enrollment_type in enrollment_types:
            choices.append((enrollment_type.pk, enrollment_type.text))

        self.fields['enrollment_type'] = forms.TypedChoiceField(
            choices=choices,
            required=True,
            label='',
            widget=frontend.forms.SistemaRadioSelect(attrs={
                'theme': 'primary',
            }),
            coerce=int,
            disabled=disabled,
        )


class SelectSessionAndParallelForm(forms.Form):
    def __init__(self, sessions_and_parallels, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for session_and_parallel in sessions_and_parallels:
            full_parallel_name = '%s. Параллель %s' % (
                session_and_parallel.session.get_full_name(),
                session_and_parallel.parallel.name
            )
            choices.append((session_and_parallel.pk, full_parallel_name))

        self.fields['session_and_parallel'] = forms.TypedChoiceField(
            choices=choices,
            required=True,
            label='',
            widget=frontend.forms.SistemaRadioSelect(attrs={
                'theme': 'primary',
            }),
            coerce=int,
        )
