# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-31 09:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('schools', '0008_auto_20160528_1748'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием', max_length=100)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SettingsItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием', max_length=100)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('app', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BigIntegerSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.BigIntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='CharSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='DateSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.DateField()),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='DateTimeSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='EmailSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.EmailField(max_length=254)),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='IntegerSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='PositiveIntegerSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.PositiveIntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.CreateModel(
            name='TextSettingsItem',
            fields=[
                ('settingsitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sistema.SettingsItem')),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('sistema.settingsitem',),
        ),
        migrations.AddField(
            model_name='settingsitem',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sistema.Group'),
        ),
        migrations.AddField(
            model_name='settingsitem',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_sistema.settingsitem_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='settingsitem',
            name='school',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='schools.School'),
        ),
        migrations.AddField(
            model_name='settingsitem',
            name='session',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='schools.Session'),
        ),
    ]
