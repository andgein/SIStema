# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-11 08:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_auto_20180305_2047'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='abstractgroup',
            options={'verbose_name': 'group'},
        ),
        migrations.AlterModelOptions(
            name='groupaccess',
            options={'verbose_name': 'group access', 'verbose_name_plural': 'group accesses'},
        ),
    ]
