# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-06 20:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20160730_2222'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=100, verbose_name='Имя')),
                ('middle_name', models.CharField(blank=True, max_length=100, verbose_name='Отчество')),
                ('last_name', models.CharField(blank=True, max_length=100, verbose_name='Фамилия')),
                ('sex', models.PositiveIntegerField(choices=[(1, 'женский'), (2, 'мужской')], blank=True, null=True, validators=[djchoices.choices.ChoicesValidator({1: 'женский', 2: 'мужской'})], verbose_name='Пол')),
                ('birth_date', models.DateField(verbose_name='Дата рождения', blank=True, null=True)),
                ('_zero_class_year', models.PositiveIntegerField(db_column='zero_class_year', help_text='используется для вычисления текущего класса', blank=True, null=True, verbose_name='Год поступления в "нулевой" класс')),
                ('region', models.CharField(blank=True, help_text='или страна, если не Россия', max_length=100, verbose_name='Субъект РФ')),
                ('city', models.CharField(blank=True, help_text='в котором находится школа', max_length=100, verbose_name='Населённый пункт')),
                ('school_name', models.CharField(blank=True, max_length=100, verbose_name='Школа')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Телефон')),
                ('citizenship', models.IntegerField(choices=[(1, 'Россия'), (2, 'Казахстан'), (3, 'Беларусь'), (4, 'Таджикистан'), (-1, 'Другое')], blank=True, null=True, validators=[djchoices.choices.ChoicesValidator({-1: 'Другое', 1: 'Россия', 2: 'Казахстан', 3: 'Беларусь', 4: 'Таджикистан'})], verbose_name='Гражданство')),
                ('citizenship_other', models.CharField(blank=True, max_length=100, verbose_name='Другое гражданство')),
                ('document_type', models.IntegerField(choices=[(1, 'Российский паспорт'), (2, 'Свидетельство о рождении'), (3, 'Заграничный паспорт'), (4, 'Паспорт другого государства'), (-1, 'Другой')], blank=True, null=True, validators=[djchoices.choices.ChoicesValidator({-1: 'Другой', 1: 'Российский паспорт', 2: 'Свидетельство о рождении', 3: 'Заграничный паспорт', 4: 'Паспорт другого государства'})], verbose_name='Тип документа')),
                ('document_number', models.CharField(blank=True, max_length=20, verbose_name='Номер документа')),
                ('insurance_number', models.CharField(blank=True, max_length=20, verbose_name='Номер медицинского полиса')),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
