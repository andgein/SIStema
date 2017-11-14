# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def make_key_dates(apps, _schema_editor):
    Questionnaire = apps.get_model('questionnaire', 'Questionnaire')
    KeyDate = apps.get_model('dates', 'KeyDate')
    for questionnaire in Questionnaire.objects.all():
        if questionnaire.close_time is not None:
            if questionnaire.school is None:
                questionnaire_name = questionnaire.title
            else:
                questionnaire_name = '{}. {}'.format(questionnaire.school.name,
                                                     questionnaire.title)
            questionnaire.close_time_key_date = KeyDate.objects.create(
                datetime=questionnaire.close_time,
                name='Дедлайн для анкеты "{}"'.format(questionnaire_name),
            )
            questionnaire.save()


def make_key_dates_reverse(apps, _schema_editor):
    Questionnaire = apps.get_model('questionnaire', 'Questionnaire')
    for questionnaire in Questionnaire.objects.all():
        if questionnaire.close_time_key_date is not None:
            questionnaire.close_time = (
                questionnaire.close_time_key_date.datetime)
            questionnaire.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dates', '0001_initial'),
        ('questionnaire', '0006_merge_20170523_0716'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='close_time_key_date',
            field=models.ForeignKey(blank=True, help_text='Начиная с этого момента пользователи видят анкету в режиме только для чтения', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='dates.KeyDate', verbose_name='Время закрытия'),
        ),
        migrations.RunPython(
            code=make_key_dates,
            reverse_code=make_key_dates_reverse,
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='close_time',
        ),
        migrations.RenameField(
            model_name='questionnaire',
            old_name='close_time_key_date',
            new_name='close_time',
        )
    ]
