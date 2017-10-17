# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-09 09:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0015_auto_20170617_1842'),
        ('poldnev', '0009_auto_20170323_0029'),
    ]

    operations = [
        migrations.AddField(
            model_name='studygroup',
            name='schools_group',
            field=models.OneToOneField(blank=True, help_text='Группа из модуля schools, соответствующая этой группе на poldnev.ru', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='poldnev_group', to='schools.Group'),
        ),
    ]