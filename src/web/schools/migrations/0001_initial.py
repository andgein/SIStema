# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='I.e. SIS 2015', max_length=50)),
                ('short_name', models.CharField(max_length=20, help_text='Used in page urls, i.e. sis2015', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='I.e. August', max_length=50)),
                ('short_name', models.CharField(help_text='Used in page urls, i.e. august', max_length=20)),
                ('school', models.ForeignKey(to='schools.School', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='session',
            unique_together=set([('school', 'short_name')]),
        ),
    ]
