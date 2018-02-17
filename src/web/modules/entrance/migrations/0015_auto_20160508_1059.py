# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djchoices.choices
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0004_auto_20160508_1059'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entrance', '0014_auto_20160507_1540'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckingComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('commented_by', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='schools.School')),
                ('for_user', models.ForeignKey(on_delete=models.CASCADE, related_name='checking_comments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EntranceRecommendation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('checked_by', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, related_name='+', to='schools.School')),
                ('for_user', models.ForeignKey(on_delete=models.CASCADE, related_name='entrance_recommendations', to=settings.AUTH_USER_MODEL)),
                ('parallel', models.ForeignKey(on_delete=models.CASCADE, related_name='entrance_recommendations', to='schools.Parallel')),
            ],
        ),
        migrations.CreateModel(
            name='EntranceStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('public_comment', models.TextField(help_text='Публичный комментарий. Может быть виден поступающему')),
                ('is_status_visible', models.BooleanField()),
                ('status', models.IntegerField(choices=[(1, 'Не участвовал в конкурсе'), (2, 'Автоматический отказ'), (3, 'Не прошёл по конкурсу'), (4, 'Поступил')], validators=[djchoices.choices.ChoicesValidator({1: 'Не участвовал в конкурсе', 2: 'Автоматический отказ', 3: 'Не прошёл по конкурсу', 4: 'Поступил'})])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=models.CASCADE, null=True, blank=True, to=settings.AUTH_USER_MODEL, default=None)),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, related_name='entrance_statuses', to='schools.School')),
                ('for_user', models.ForeignKey(on_delete=models.CASCADE, related_name='entrance_statuses', to=settings.AUTH_USER_MODEL)),
                ('parallel', models.ForeignKey(on_delete=models.CASCADE, null=True, blank=True, to='schools.Parallel', default=None)),
                ('session', models.ForeignKey(on_delete=models.CASCADE, null=True, blank=True, to='schools.Session', default=None)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='entrancestatus',
            unique_together=set([('for_school', 'for_user')]),
        ),
    ]
