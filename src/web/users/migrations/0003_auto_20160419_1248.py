# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from django.utils import crypto
import users.models
import django.core.validators


def generate_random_secret_string():
    return crypto.get_random_string(length=32)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_enlarge_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPasswordRecovery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('recovery_token', models.CharField(default=generate_random_secret_string, max_length=32)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='userpasswordrecovery',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
