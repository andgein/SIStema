# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-22 00:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smartq', '0002_auto_20170318_2159'),
        ('topics', '0005_auto_20170319_1622'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionForTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mark', models.PositiveIntegerField(help_text='Question will be asked is this mark is equal to user mark for topic')),
                ('group', models.IntegerField(blank=True, default=None, help_text='Same group indicates similar questions, e.g. bfs/dfs, and only one of them is asked', null=True)),
                ('scale_in_topic', models.ForeignKey(help_text='Question is for this topic', on_delete=django.db.models.deletion.CASCADE, related_name='smartq_mapping', to='topics.ScaleInTopic')),
                ('smartq_question', models.ForeignKey(help_text='Base checking question without specified numbers', on_delete=django.db.models.deletion.CASCADE, related_name='topic_mapping', to='smartq.Question')),
            ],
        ),
        migrations.RemoveField(
            model_name='topicquestionmapping',
            name='question',
        ),
        migrations.RemoveField(
            model_name='topicquestionmapping',
            name='scale_in_topic',
        ),
        migrations.RenameField(
            model_name='smartqquestionnaire',
            old_name='creation_date',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='smartqquestionnaire',
            old_name='topics',
            new_name='topic_questionnaire',
        ),
        migrations.RenameField(
            model_name='smartqquestionnairequestion',
            old_name='question',
            new_name='generated_question',
        ),
        migrations.AlterField(
            model_name='smartqquestionnairequestion',
            name='topic_mapping',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='topics.QuestionForTopic'),
        ),
        migrations.DeleteModel(
            name='TopicQuestionMapping',
        ),
    ]
