# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('ejudge', '0003_auto_20160329_1823'),
    ]

    operations = [
        migrations.AddField(
            model_name='queueelement',
            name='wont_check_message',
            field=models.TextField(default='', blank=True),
        ),
        migrations.AlterField(
            model_name='queueelement',
            name='status',
            field=models.PositiveIntegerField(default=1, validators=[djchoices.choices.ChoicesValidator({1: 'NOT FETCHED', 2: 'SUBMITTED', 3: 'CHECKED', 4: 'WONT CHECK'})], choices=[(1, 'NOT FETCHED'), (2, 'SUBMITTED'), (3, 'CHECKED'), (4, 'WONT CHECK')]),
        ),
        migrations.AlterField(
            model_name='queueelement',
            name='submission',
            field=models.ForeignKey(default=None, on_delete=models.CASCADE, blank=True, to='ejudge.Submission', null=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='result',
            field=models.ForeignKey(default=None, on_delete=models.CASCADE, blank=True, to='ejudge.SolutionCheckingResult', null=True),
        ),
    ]
