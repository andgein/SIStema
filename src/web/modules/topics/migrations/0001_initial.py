# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
from django.conf import settings
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0003_school_full_name'),
        ('entrance', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupUserMark',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('mark', models.PositiveIntegerField()),
                ('is_automatically', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EntranceLevelRequirement',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('max_penalty', models.PositiveIntegerField()),
                ('entrance_level', models.ForeignKey(on_delete=models.CASCADE, to='entrance.EntranceLevel')),
            ],
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='LevelDownwardDependency',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('min_percent', models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='Процент не может быть меньше нуля'), django.core.validators.MaxValueValidator(100, message='Процент не может быть больше 100')], help_text='Минимальный процент максимальных/минимальных оценок из source_level')),
                ('destination_level', models.ForeignKey(on_delete=models.CASCADE, to='topics.Level', related_name='+')),
            ],
            options={
                'verbose_name_plural': 'Level downward dependencies',
            },
        ),
        migrations.CreateModel(
            name='LevelUpwardDependency',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('min_percent', models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='Процент не может быть меньше нуля'), django.core.validators.MaxValueValidator(100, message='Процент не может быть больше 100')], help_text='Минимальный процент максимальных/минимальных оценок из source_level')),
                ('destination_level', models.ForeignKey(on_delete=models.CASCADE, to='topics.Level', related_name='+')),
            ],
            options={
                'verbose_name_plural': 'Level upward dependencies',
            },
        ),
        migrations.CreateModel(
            name='Scale',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(unique=True, max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')),
                ('title', models.CharField(max_length=100, help_text='Например, «Практика». Показывается школьнику')),
                ('count_values', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ScaleInTopic',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ScaleInTopicIssue',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ScaleLabel',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('mark', models.PositiveIntegerField()),
                ('label_text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ScaleLabelGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')),
                ('scale', models.ForeignKey(on_delete=models.CASCADE, to='topics.Scale', related_name='label_groups')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(unique=True, max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')),
                ('title', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(unique=True, max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')),
                ('title', models.CharField(max_length=100, help_text='Показывается школьнику при заполнении анкеты')),
                ('text', models.TextField(help_text='Более подробное описание. Показывается школьнику при заполнении анкеты')),
                ('order', models.IntegerField(default=0, help_text='Внутренний порядок возрастания сложности')),
                ('level', models.ForeignKey(on_delete=models.CASCADE, to='topics.Level')),
            ],
        ),
        migrations.CreateModel(
            name='TopicDependency',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('source_mark', models.PositiveIntegerField()),
                ('destination_mark', models.PositiveIntegerField()),
                ('destination', models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleInTopic', related_name='dependencies_as_destination_topic')),
                ('source', models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleInTopic', related_name='dependencies_as_source_topic')),
            ],
            options={
                'verbose_name_plural': 'Topic dependencies',
            },
        ),
        migrations.CreateModel(
            name='TopicIssue',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_correcting', models.BooleanField(default=False)),
                ('topic', models.ForeignKey(on_delete=models.CASCADE, to='topics.Topic')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TopicQuestionnaire',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('for_school', models.OneToOneField(to='schools.School', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='UserMark',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('mark', models.PositiveIntegerField()),
                ('is_automatically', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('scale_in_topic', models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleInTopic')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserQuestionnaireStatus',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('status', models.PositiveIntegerField(choices=[(1, 'NOT STARTED'), (2, 'STARTED'), (3, 'CORRECTING'), (4, 'FINISHED')], validators=[djchoices.choices.ChoicesValidator({1: 'NOT STARTED', 2: 'STARTED', 3: 'CORRECTING', 4: 'FINISHED'})])),
                ('questionnaire', models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire', related_name='+')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, related_name='+')),
            ],
            options={
                'verbose_name_plural': 'User questionnaire statuses',
            },
        ),
        migrations.AddField(
            model_name='topic',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='topic',
            name='tags',
            field=models.ManyToManyField(to='topics.Tag', related_name='topics'),
        ),
        migrations.AddField(
            model_name='tag',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='scalelabel',
            name='group',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleLabelGroup', related_name='labels'),
        ),
        migrations.AddField(
            model_name='scaleintopicissue',
            name='label_group',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleLabelGroup'),
        ),
        migrations.AddField(
            model_name='scaleintopicissue',
            name='topic_issue',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicIssue', related_name='scales'),
        ),
        migrations.AddField(
            model_name='scaleintopic',
            name='scale_label_group',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleLabelGroup'),
        ),
        migrations.AddField(
            model_name='scaleintopic',
            name='topic',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.Topic'),
        ),
        migrations.AddField(
            model_name='scale',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='levelupwarddependency',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='levelupwarddependency',
            name='source_level',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.Level', related_name='+'),
        ),
        migrations.AddField(
            model_name='leveldownwarddependency',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='leveldownwarddependency',
            name='source_level',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.Level', related_name='+'),
        ),
        migrations.AddField(
            model_name='level',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='entrancelevelrequirement',
            name='questionnaire',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.TopicQuestionnaire'),
        ),
        migrations.AddField(
            model_name='entrancelevelrequirement',
            name='tag',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.Tag'),
        ),
        migrations.AddField(
            model_name='backupusermark',
            name='scale_in_topic',
            field=models.ForeignKey(on_delete=models.CASCADE, to='topics.ScaleInTopic'),
        ),
        migrations.AddField(
            model_name='backupusermark',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='userquestionnairestatus',
            unique_together=set([('user', 'questionnaire')]),
        ),
        migrations.AlterUniqueTogether(
            name='usermark',
            unique_together=set([('user', 'scale_in_topic')]),
        ),
        migrations.AlterIndexTogether(
            name='topicdependency',
            index_together=set([('source', 'source_mark'), ('source', 'destination')]),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('questionnaire', 'short_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='scalelabelgroup',
            unique_together=set([('scale', 'short_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='scaleintopic',
            unique_together=set([('topic', 'scale_label_group')]),
        ),
        migrations.AlterUniqueTogether(
            name='entrancelevelrequirement',
            unique_together=set([('questionnaire', 'entrance_level', 'tag')]),
        ),
        migrations.AlterUniqueTogether(
            name='backupusermark',
            unique_together=set([('user', 'scale_in_topic')]),
        ),
    ]
