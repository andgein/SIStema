# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProgrammingLanguage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием', max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('ejudge_id', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='QueueElement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program', models.TextField()),
                ('status', models.PositiveIntegerField(choices=[(1, 'NOT FETCHED'), (2, 'SUBMITTED'), (3, 'CHECKED')], validators=[djchoices.choices.ChoicesValidator({1: 'NOT FETCHED', 2: 'SUBMITTED', 3: 'CHECKED'})], default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('language', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ejudge.ProgrammingLanguage')),
            ],
        ),
        migrations.CreateModel(
            name='SolutionCheckingResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.PositiveIntegerField(choices=[(0, 'OK'), (1, 'COMPILE ERROR'), (2, 'RUNTIME ERROR'), (3, 'TIME LIMIT ERROR'), (4, 'PRESENTATION ERROR'), (5, 'WRONG ANSWER ERROR'), (6, 'CHECK FAILED ERROR'), (12, 'MEMORY LIMIT ERROR'), (13, 'SECURITY ERROR'), (14, 'STYLE ERROR'), (15, 'WALL TIME LIMIT ERROR'), (18, 'SKIPPED')], validators=[djchoices.choices.ChoicesValidator({0: 'OK', 1: 'COMPILE ERROR', 2: 'RUNTIME ERROR', 3: 'TIME LIMIT ERROR', 4: 'PRESENTATION ERROR', 5: 'WRONG ANSWER ERROR', 6: 'CHECK FAILED ERROR', 12: 'MEMORY LIMIT ERROR', 13: 'SECURITY ERROR', 14: 'STYLE ERROR', 15: 'WALL TIME LIMIT ERROR', 18: 'SKIPPED'})])),
                ('score', models.PositiveIntegerField()),
                ('max_possible_score', models.PositiveIntegerField()),
                ('time_elapsed', models.FloatField()),
                ('memory_consumed', models.PositiveIntegerField(help_text='В байтах')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ejudge_contest_id', models.PositiveIntegerField()),
                ('ejudge_submit_id', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('result', models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to='ejudge.SolutionCheckingResult')),
            ],
        ),
        migrations.CreateModel(
            name='TestCheckingResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.PositiveIntegerField(choices=[(0, 'OK'), (1, 'COMPILE ERROR'), (2, 'RUNTIME ERROR'), (3, 'TIME LIMIT ERROR'), (4, 'PRESENTATION ERROR'), (5, 'WRONG ANSWER ERROR'), (6, 'CHECK FAILED ERROR'), (12, 'MEMORY LIMIT ERROR'), (13, 'SECURITY ERROR'), (14, 'STYLE ERROR'), (15, 'WALL TIME LIMIT ERROR'), (18, 'SKIPPED')], validators=[djchoices.choices.ChoicesValidator({0: 'OK', 1: 'COMPILE ERROR', 2: 'RUNTIME ERROR', 3: 'TIME LIMIT ERROR', 4: 'PRESENTATION ERROR', 5: 'WRONG ANSWER ERROR', 6: 'CHECK FAILED ERROR', 12: 'MEMORY LIMIT ERROR', 13: 'SECURITY ERROR', 14: 'STYLE ERROR', 15: 'WALL TIME LIMIT ERROR', 18: 'SKIPPED'})])),
                ('score', models.PositiveIntegerField()),
                ('max_possible_score', models.PositiveIntegerField()),
                ('time_elapsed', models.FloatField()),
                ('memory_consumed', models.PositiveIntegerField(help_text='В байтах')),
                ('solution_checking_result', models.ForeignKey(related_name='tests', on_delete=models.CASCADE, to='ejudge.SolutionCheckingResult')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='queueelement',
            name='submission',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to='ejudge.Submission'),
        ),
    ]
