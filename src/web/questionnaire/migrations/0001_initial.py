# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0002_auto_20160320_1808'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChoiceQuestionnaireQuestion',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('short_name', models.CharField(help_text='Идентификатор. Лучше сделать из английских букв, цифр и подчёркивания', max_length=100)),
                ('text', models.CharField(help_text='Вопрос', max_length=100)),
                ('is_required', models.BooleanField(help_text='Является ли вопрос обязательным')),
                ('help_text', models.CharField(help_text='Подсказка, помогающая ответить на вопрос', blank=True, max_length=400)),
                ('Порядок', models.IntegerField(help_text='Вопросы выстраиваются по возрастанию порядка', default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChoiceQuestionnaireQuestionVariant',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('text', models.CharField(max_length=100)),
                ('is_multiple', models.BooleanField()),
                ('is_inline', models.BooleanField()),
                ('question', models.ForeignKey(on_delete=models.CASCADE, to='questionnaire.ChoiceQuestionnaireQuestion', related_name='variants')),
            ],
        ),
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('short_name', models.CharField(help_text='Используется для урлов. Лучше обойтись латинскими букваи, цифрами и подчёркиванием', max_length=100)),
                ('title', models.CharField(help_text='Название анкеты', max_length=100)),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, to='schools.School', blank=True)),
                ('for_session', models.ForeignKey(on_delete=models.CASCADE, to='schools.Session', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TextQuestionnaireQuestion',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('short_name', models.CharField(help_text='Идентификатор. Лучше сделать из английских букв, цифр и подчёркивания', max_length=100)),
                ('text', models.CharField(help_text='Вопрос', max_length=100)),
                ('is_required', models.BooleanField(help_text='Является ли вопрос обязательным')),
                ('help_text', models.CharField(help_text='Подсказка, помогающая ответить на вопрос', blank=True, max_length=400)),
                ('Порядок', models.IntegerField(help_text='Вопросы выстраиваются по возрастанию порядка', default=0)),
                ('is_multiline', models.BooleanField()),
                ('questionnaire', models.ForeignKey(on_delete=models.CASCADE, to='questionnaire.Questionnaire', related_name='textquestionnairequestion_questions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='YesNoQuestionnaireQuestion',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('short_name', models.CharField(help_text='Идентификатор. Лучше сделать из английских букв, цифр и подчёркивания', max_length=100)),
                ('text', models.CharField(help_text='Вопрос', max_length=100)),
                ('is_required', models.BooleanField(help_text='Является ли вопрос обязательным')),
                ('help_text', models.CharField(help_text='Подсказка, помогающая ответить на вопрос', blank=True, max_length=400)),
                ('Порядок', models.IntegerField(help_text='Вопросы выстраиваются по возрастанию порядка', default=0)),
                ('questionnaire', models.ForeignKey(on_delete=models.CASCADE, to='questionnaire.Questionnaire', related_name='yesnoquestionnairequestion_questions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='choicequestionnairequestion',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='questionnaire.Questionnaire', related_name='choicequestionnairequestion_questions'),
        ),
        migrations.AlterUniqueTogether(
            name='questionnaire',
            unique_together=set([('for_school', 'short_name')]),
        ),
    ]
