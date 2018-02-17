# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entrance', '0012_entranceexam_close_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolutionMark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mark', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('marked_by', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('solution', models.ForeignKey(on_delete=models.CASCADE,
                                               to='entrance.EntranceExamTaskSolution')),
            ],
        ),
        migrations.AddField(
            model_name='entranceexamtask',
            name='max_mark',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
