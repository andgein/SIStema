# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-11 14:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0008_auto_20160807_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalemailuser',
            name='display_name',
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name='externalemailuser',
            name='email',
            field=models.EmailField(db_index=True, max_length=254),
        ),
    ]
