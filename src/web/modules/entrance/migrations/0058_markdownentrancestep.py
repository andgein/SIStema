# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-11 07:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0057_auto_20180309_1453'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkdownEntranceStep',
            fields=[
                ('abstractentrancestep_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='entrance.AbstractEntranceStep')),
                ('text_before_start_date', models.TextField(blank=True, help_text='Текст, который показывается до даты начала заполнения шага. Поддерживается Markdown')),
                ('text_after_finish_date_if_passed', models.TextField(blank=True, help_text='Текст, который показывается после даты окончания заполнения, если шаг выполнен. Поддерживается Markdown')),
                ('text_after_finish_date_if_not_passed', models.TextField(blank=True, help_text='Текст, который показывается после даты окончания заполнения, если шаг не выполнен. Поддерживается Markdown')),
                ('text_waiting_for_other_step', models.TextField(blank=True, help_text='Текст, который показывается, когда не пройден один из предыдущих шагов. Поддерживается Markdown')),
                ('text_step_is_not_passed', models.TextField(blank=True, help_text='Текст, который показывается, когда шаг ещё не пройден. Поддерживается Markdown')),
                ('text_step_is_passed', models.TextField(blank=True, help_text='Текст, который показывается, когда шаг пройден пользователем. Поддерживается Markdown')),
                ('markdown', models.TextField(help_text='Текст, который будет показан школьникам. Поддерживается Markdown')),
            ],
            bases=('entrance.abstractentrancestep', models.Model),
        ),
    ]
