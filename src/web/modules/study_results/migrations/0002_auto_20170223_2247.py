# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-23 22:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('study_results', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='WinterComment',
            new_name='AfterWinterComment',
        ),
        migrations.RenameModel(
            old_name='WinterParticipationComment',
            new_name='AsWinterParticipantComment',
        ),
    ]
