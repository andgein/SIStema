# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0006_auto_20160405_0300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entrancelevelupgrade',
            name='upgraded_to',
            field=models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='entrance.EntranceLevel'),
        ),
    ]
