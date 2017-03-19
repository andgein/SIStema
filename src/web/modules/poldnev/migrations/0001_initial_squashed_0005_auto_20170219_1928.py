# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-19 18:52
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('poldnev', '0001_initial'), ('poldnev', '0002_auto_20170126_2208'), ('poldnev', '0003_auto_20170212_2033'), ('poldnev', '0004_auto_20170219_1918'), ('poldnev', '0005_auto_20170219_1928')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schools', '0009_auto_20170115_2213'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poldnev_id', models.IntegerField(help_text='Id человека на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', unique=True)),
                ('first_name', models.CharField(help_text='Имя человека на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', max_length=100)),
                ('middle_name', models.CharField(help_text='Отчество человека на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', max_length=100)),
                ('last_name', models.CharField(help_text='Фамилия человека на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', max_length=200)),
                ('verified', models.BooleanField(default=False, help_text='True, если корректность значения user была проверена человеком')),
                ('user', models.OneToOneField(help_text='Пользователь, соответствующий этому человеку на poldnev.ru', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='poldnev', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poldnev_role', models.CharField(help_text='Строка, обозначающая роль на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poldnev_id', models.CharField(help_text='Id смены на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', max_length=50, unique=True)),
                ('name', models.CharField(help_text='Имя смены на poldnev.ru. Заполняется автоматически командой manage.py update_poldnev по информации с сайта.', max_length=50)),
                ('verified', models.BooleanField(default=False, help_text='True, если корректность значения schools_session была проверена человеком')),
                ('schools_session', models.OneToOneField(help_text='Смена из модуля schools, соответствующая этой смене на poldnev.ru', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='poldnev', to='schools.Session')),
                ('url', models.URLField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='role',
            name='session',
            field=models.ForeignKey(help_text='Смена из модуля schools, соответствующая этой смене на poldnev.ru', on_delete=django.db.models.deletion.CASCADE, to='poldnev.Session'),
        ),
        migrations.AddField(
            model_name='historyentry',
            name='person',
            field=models.ForeignKey(help_text='Человек', on_delete=django.db.models.deletion.CASCADE, to='poldnev.Person'),
        ),
        migrations.AddField(
            model_name='historyentry',
            name='role',
            field=models.ForeignKey(help_text='Роль. Также содержит информацию о смене.', on_delete=django.db.models.deletion.CASCADE, to='poldnev.Role'),
        ),
        migrations.AlterModelOptions(
            name='person',
            options={'ordering': ('last_name', 'first_name', 'middle_name')},
        ),
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ('-poldnev_id',)},
        ),
    ]
