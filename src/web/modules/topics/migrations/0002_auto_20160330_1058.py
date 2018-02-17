# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userquestionnairestatus',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire', related_name='statuses'),
        ),
    ]
