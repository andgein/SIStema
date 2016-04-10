# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-10 21:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0007_auto_20160405_0347'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntranceLevelUpgradeRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SolveTaskEntranceLevelUpgradeRequirement',
            fields=[
                ('entrancelevelupgraderequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='entrance.EntranceLevelUpgradeRequirement')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='entrance.EntranceExamTask')),
            ],
            bases=('entrance.entrancelevelupgraderequirement',),
        ),
        migrations.AddField(
            model_name='entrancelevelupgraderequirement',
            name='base_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='entrance.EntranceLevel'),
        ),
    ]
