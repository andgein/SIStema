from django import forms

import frontend.forms


class FileEntranceExamTasksMarkForm(forms.Form):
    FIELD_ID_TEMPLATE = 'tasks__file__mark_%d'
    COMMENT_ID_TEMPLATE = 'tasks__file__comment_%d'

    def __init__(self, tasks, *args, **kwargs):
        with_comment = kwargs.pop('with_comment', False)
        super().__init__(*args, **kwargs)

        for task in tasks:
            field_id = self.FIELD_ID_TEMPLATE % task.id
            self.fields[field_id] = forms.IntegerField(
                min_value=0,
                max_value=task.max_score,
                widget=forms.HiddenInput(attrs={'id': field_id}),
            )
            self.fields[field_id].task_id = task.id
            if with_comment:
                comment_field_id = self.COMMENT_ID_TEMPLATE % task.id
                self.fields[comment_field_id] = forms.CharField(
                    label_suffix='',
                    label='',
                    widget=frontend.forms.TextareaWithFaIcon(attrs={
                        'fa': 'comment',
                        'id': comment_field_id,
                        'placeholder': 'Комментарий о решении',
                        'class': 'form-control',
                        'rows': 3
                    }),
                    required=False
                )

    def set_initial_mark(self, task_id, mark):
        field_id = self.FIELD_ID_TEMPLATE % task_id
        self.fields[field_id].initial = mark


class EntranceRecommendationForm(forms.Form):
    comment = forms.CharField(widget=frontend.forms.TextInputWithFaIcon(attrs={'fa': 'comment'}),
                              label='Комментарий',
                              required=False)

    score = forms.IntegerField(label='Баллы', initial=0)

    RECOMMENDED_PARALLEL_UNFILLED = -2

    recommended_parallel = forms.TypedChoiceField(widget=forms.Select(),
                                                  label='Рекомендованная параллель',
                                                  coerce=int,
                                                  )

    def __init__(self, school, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parallels = school.parallels.all()
        parallels = [(p.id, p.name) for p in parallels]

        available_parallels = [(self.RECOMMENDED_PARALLEL_UNFILLED, 'Выберите параллель'), (-1, 'Не зачислить')] + list(parallels)
        self.fields['recommended_parallel'].choices = available_parallels


class AddCheckingCommentForm(forms.Form):
    comment = forms.CharField(
        required=True,
        error_messages={
            'required': 'Напишите комментарий',
        },
        label='',
        label_suffix='',
        widget=frontend.forms.SistemaTextarea(
            fa='comment',
            attrs={
                'placeholder': 'Добавить комментарий',
                'class': 'one-line',
                'rows': 1
            },
        )
    )
