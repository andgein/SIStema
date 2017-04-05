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
        max_upload_size=512 * 1024,
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

    def __init__(self, task, *args, **kwargs):
        super().__init__(task, *args, **kwargs)
        if task.problem_type == task.ProblemType.OUTPUT_ONLY:
            del self.fields['language']
            self.fields['solution'].label = 'Выберите файл'
