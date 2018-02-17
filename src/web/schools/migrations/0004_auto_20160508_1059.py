# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0003_school_full_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parallel',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('short_name', models.CharField(max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием. Например, cprime')),
                ('name', models.CharField(max_length=100, help_text="Например, C'")),
                ('school', models.ForeignKey(to='schools.School', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterField(
            model_name='session',
            name='short_name',
            field=models.CharField(max_length=20, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием. Например, august'),
        ),
        migrations.AddField(
            model_name='parallel',
            name='sessions',
            field=models.ManyToManyField(to='schools.Session'),
        ),
        migrations.AlterUniqueTogether(
            name='parallel',
            unique_together=set([('school', 'short_name')]),
        ),
    ]
