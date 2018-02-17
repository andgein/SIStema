# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('questionnaire', '0005_auto_20160325_0105'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireAnswer',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('question_short_name', models.CharField(max_length=100)),
                ('answer', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserQuestionnaireStatus',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('status', models.PositiveIntegerField(choices=[(1, 'NOT FILLED'), (2, 'FILLED')], validators=[djchoices.choices.ChoicesValidator({1: 'NOT FILLED', 2: 'FILLED'})])),
            ],
            options={
                'verbose_name_plural': 'User questionnaire statuses',
            },
        ),
        migrations.RemoveField(
            model_name='choicequestionnairequestionvariant',
            name='is_inline',
        ),
        migrations.RemoveField(
            model_name='choicequestionnairequestionvariant',
            name='is_multiple',
        ),
        migrations.AddField(
            model_name='choicequestionnairequestion',
            name='is_inline',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='choicequestionnairequestion',
            name='is_multiple',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='short_name',
            field=models.CharField(max_length=100, help_text='Используется для урлов. Лучше обойтись латинскими буквами, цифрами и подчёркиванием'),
        ),
        migrations.AddField(
            model_name='userquestionnairestatus',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='questionnaire.Questionnaire'),
        ),
        migrations.AddField(
            model_name='userquestionnairestatus',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='questionnaireanswer',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='questionnaire.Questionnaire'),
        ),
        migrations.AddField(
            model_name='questionnaireanswer',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='userquestionnairestatus',
            unique_together=set([('user', 'questionnaire')]),
        ),
        migrations.AlterUniqueTogether(
            name='questionnaireanswer',
            unique_together=set([('questionnaire', 'user', 'question_short_name')]),
        ),
    ]
