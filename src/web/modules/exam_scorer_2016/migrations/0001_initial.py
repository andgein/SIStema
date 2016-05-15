# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-29 21:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('entrance', '0012_entranceexam_close_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntranceExamScorer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('max_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='entrance.EntranceLevel')),
            ],
        ),
        migrations.CreateModel(
            name='ProgramTaskScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('scorer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam_scorer_2016.EntranceExamScorer')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='entrance.ProgramEntranceExamTask')),
            ],
        ),
        migrations.CreateModel(
            name='TestCountScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField()),
                ('score', models.IntegerField()),
                ('scorer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam_scorer_2016.EntranceExamScorer')),
            ],
        ),
    ]