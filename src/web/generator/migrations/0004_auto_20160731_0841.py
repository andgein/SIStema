# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-31 08:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import relativefilepathfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('generator', '0003_auto_20160725_1510'),
    ]

    operations = [
        migrations.AlterField(
            model_name='font',
            name='filename',
            field=relativefilepathfield.fields.RelativeFilePathField(match='.*\\.ttf', max_length=1000, path=settings.SISTEMA_GENERATOR_FONTS_DIR, recursive=True),
        ),
        migrations.AlterField(
            model_name='linetablestylecommand',
            name='command_name',
            field=models.CharField(choices=[('BOX', 'Box'), ('LINEAFTER', 'Lineafter'), ('LINEBEFORE', 'Linebefore'), ('OUTLINE', 'Outline'), ('LINEABOVE', 'Lineabove'), ('INNERGRID', 'Innergrid'), ('GRID', 'Grid'), ('LINEBELOW', 'Linebelow')], max_length=100),
        ),
    ]
