# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0006_auto_20160328_0243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userquestionnairestatus',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='questionnaire.Questionnaire', related_name='statuses'),
        ),
    ]
