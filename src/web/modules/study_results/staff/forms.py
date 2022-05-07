from django import forms
from frontend.forms import RestrictedFileField


class UploadStudyResultsForm(forms.Form):
    file = RestrictedFileField(
        max_upload_size=10 * 1024 * 1024,
        required=True,
        help_text='CSV-файл с оценками и комментариями'
    )

    user_id_field_name = forms.CharField(
        help_text="Поле c sis_id",
        initial="sis_id",
        required=True,
    )

    parallel_field_name = forms.CharField(
        help_text='Поле с параллелью или группой',
        initial='Группа',
        required=True,
    )

    theory_field_name = forms.CharField(
        help_text='Поле с оценкой за теорию',
        initial='Теория',
        required=True,
    )

    practice_field_name = forms.CharField(
        help_text='Поле с оценкой за практику',
        initial='Практика',
        required=True,
    )

    study_comment_field_name = forms.CharField(
        help_text='Поле с комментарием по учёбе',
        initial='Комментарий по учебе',
        required=False,
    )

    social_comment_field_name = forms.CharField(
        help_text='Поле с комментарием по внеучебной деятельности',
        initial='Комментарий по внеучебной деятельности',
        required=False,
    )

    as_winter_participant_field_name = forms.CharField(
        help_text='Поле о том, брать ли в зиму',
        initial='Брать ли в зиму',
        required=False,
    )

    next_year_field_name = forms.CharField(
        help_text='Поле о том, куда брать в следующем году',
        initial='Куда брать в следующем году',
        required=False,
    )

    as_teacher_field_name = forms.CharField(
        help_text='Поле о том, брать ли препом',
        initial='Брать ли препом',
        required=False,
    )

    after_winter_field_name = forms.CharField(
        help_text='Поле с комментарием с Зимы',
        initial='Комментарий с зимы',
        required=False,
    )
