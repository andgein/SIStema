# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def make_key_dates(apps, _schema_editor):
    AbstractEntranceStep = apps.get_model('entrance', 'AbstractEntranceStep')
    KeyDate = apps.get_model('dates', 'KeyDate')

    # artemtab: As I understand it, we don't have usual polymorphic behavior
    # here, because django restores historical model classes from db data
    # instead of using the original model class.
    # Though, it shouldn't be the problem for us, because we only want to
    # modify fields on the original AbstractEntranceStep table.
    for step in AbstractEntranceStep.objects.all():
        if step.available_from_time is not None:
            # Using (school, order) pair as step identifier as we don't have
            # the original __str__ method here
            step.available_from_time_key_date = KeyDate.objects.create(
                datetime=step.available_from_time,
                name='Начало для шага "{}: {}"'.format(step.school.name,
                                                       step.order),
            )
            step.save()

        if step.available_to_time is not None:
            # Using (school, order) pair as step identifier as we don't have
            # the original __str__ method here
            step.available_to_time_key_date = KeyDate.objects.create(
                datetime=step.available_to_time,
                name='Дедлайн для шага "{}: {}"'.format(step.school.name,
                                                        step.order),
            )
            step.save()


def make_key_dates_reverse(apps, _schema_editor):
    AbstractEntranceStep = apps.get_model('entrance', 'AbstractEntranceStep')

    # artemtab: As I understand it, we don't have usual polymorphic behavior
    # here, because django restores historical model classes from db data
    # instead of using the original model class.
    # Though, it shouldn't be the problem for us, because we only want to
    # modify fields on the original AbstractEntranceStep table.
    for step in AbstractEntranceStep.objects.all():
        if step.available_from_time_key_date is not None:
            step.available_from_time = (
                step.available_from_time_key_date.datetime)
            step.save()

        if step.available_to_time is not None:
            step.available_to_time = step.available_to_time_key_date.datetime
            step.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dates', '0001_initial'),
        ('entrance', '0051_userparticipatedinschoolentrancestepexception'),
    ]

    operations = [
        migrations.AddField(
            model_name='abstractentrancestep',
            name='available_from_time_key_date',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='dates.KeyDate', verbose_name='Доступен с'),
        ),
        migrations.AddField(
            model_name='abstractentrancestep',
            name='available_to_time_key_date',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='dates.KeyDate', verbose_name='Доступен до'),
        ),
        migrations.RunPython(
            code=make_key_dates,
            reverse_code=make_key_dates_reverse,
        ),
        migrations.RemoveField(
            model_name='abstractentrancestep',
            name='available_from_time',
        ),
        migrations.RemoveField(
            model_name='abstractentrancestep',
            name='available_to_time',
        ),
        migrations.RenameField(
            model_name='abstractentrancestep',
            old_name='available_from_time_key_date',
            new_name='available_from_time',
        ),
        migrations.RenameField(
            model_name='abstractentrancestep',
            old_name='available_to_time_key_date',
            new_name='available_to_time',
        ),
    ]
