# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entrance', '0013_auto_20160507_1302'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolutionScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('scored_by', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('solution', models.ForeignKey(on_delete=models.CASCADE, to='entrance.EntranceExamTaskSolution')),
            ],
        ),
        migrations.RemoveField(
            model_name='solutionmark',
            name='marked_by',
        ),
        migrations.RemoveField(
            model_name='solutionmark',
            name='solution',
        ),
        migrations.RenameField(
            model_name='entranceexamtask',
            old_name='max_mark',
            new_name='max_score',
        ),
        migrations.DeleteModel(
            name='SolutionMark',
        ),
    ]
