# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import modules.entrance.models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0003_school_full_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entrance', '0009_entranceexamtasksolution_ip'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckingGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('short_name', models.CharField(max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')),
                ('name', models.CharField(max_length=100)),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, to='schools.School')),
            ],
        ),
        migrations.CreateModel(
            name='CheckingLock',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('locked_until', models.DateField(default=modules.entrance.models.get_locked_timeout)),
                ('locked_by', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, related_name='checking_lock')),
                ('locked_user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, related_name='checking_locked')),
            ],
        ),
        migrations.CreateModel(
            name='UserInCheckingGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=models.CASCADE, to='entrance.CheckingGroup')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AlterUniqueTogether(
            name='checkinggroup',
            unique_together=set([('for_school', 'short_name')]),
        ),
    ]
