# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-24 15:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topics', '0011_auto_20170324_1247'),
    ]

    operations = [
        migrations.AddField(
            model_name='topiccheckingquestionnaire',
            name='checked_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
