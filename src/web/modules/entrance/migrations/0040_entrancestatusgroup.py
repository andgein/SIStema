# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-26 10:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
        ('entrance', '0039_auto_20170429_1535'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntranceStatusGroup',
            fields=[
                ('abstractgroup_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='groups.AbstractGroup')),
                ('status', models.IntegerField(choices=[(1, 'Не участвовал в конкурсе'), (2, 'Автоматический отказ'), (3, 'Не прошёл по конкурсу'), (4, 'Поступил'), (5, 'Подал заявку')], validators=[djchoices.choices.ChoicesValidator({1: 'Не участвовал в конкурсе', 2: 'Автоматический отказ', 3: 'Не прошёл по конкурсу', 4: 'Поступил', 5: 'Подал заявку'})])),
            ],
            options={
                'abstract': False,
            },
            bases=('groups.abstractgroup',),
        ),
    ]