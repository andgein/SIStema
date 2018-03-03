# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def assign_schools_to_key_dates(apps, schema):
    # Go through questionnaires (and entrance steps if entrance module is here)
    questionnaire_class = apps.get_model('questionnaire', 'Questionnaire')
    questionnaires = (
        questionnaire_class.objects
        .filter(school__isnull=False, close_time__isnull=False)
        .prefetch_related('school', 'close_time'))
    for q in questionnaires:
        q.close_time.school = q.school
        q.close_time.save()

    entrance_step_class = apps.get_model('entrance', 'AbstractEntranceStep')
    entrance_steps = (
        entrance_step_class.objects
        .filter(school__isnull=False)
        .prefetch_related('school', 'available_from_time', 'available_to_time'))
    for step in entrance_steps:
        if step.available_from_time is not None:
            step.available_from_time.school = step.school
            step.available_from_time.save()
        if step.available_to_time is not None:
            step.available_to_time.school = step.school
            step.available_to_time.save()


class Migration(migrations.Migration):

    # TODO(artemtab): this migration should be set to no-op when we squash all
    #     the migrations, as it depends on entrance, which is an optional module
    dependencies = [
        ('dates', '0002_keydate_school'),
        ('questionnaire', '0008_use_dates_app_2_20171114_2309'),
        ('entrance', '0055_auto_20180217_0000'),
    ]

    operations = [
        migrations.RunPython(
            assign_schools_to_key_dates, migrations.RunPython.noop),
    ]
