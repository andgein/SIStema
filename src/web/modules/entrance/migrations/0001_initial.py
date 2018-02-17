# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0003_school_full_name'),
        ('ejudge', '0007_auto_20160329_2040'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EntranceExam',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('for_school', models.OneToOneField(to='schools.School')),
            ],
        ),
        migrations.CreateModel(
            name='EntranceExamTask',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, help_text='Название')),
                ('text', models.TextField(help_text='Формулировка задания')),
                ('help_text', models.CharField(blank=True, max_length=100, help_text='Дополнительная информация, например, сведения о формате ответа')),
            ],
        ),
        migrations.CreateModel(
            name='EntranceExamTaskSolution',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('solution', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='EntranceLevel',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=100, help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')),
                ('name', models.CharField(max_length=100)),
                ('order', models.IntegerField(default=0)),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, to='schools.School')),
            ],
            options={
                'ordering': ['for_school_id', 'order'],
            },
        ),
        migrations.CreateModel(
            name='EntranceStep',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('class_name', models.CharField(max_length=100, help_text='Путь до класса, описывающий шаг')),
                ('params', models.TextField(help_text='Параметры для шага')),
                ('order', models.IntegerField()),
                ('for_school', models.ForeignKey(on_delete=models.CASCADE, to='schools.School', related_name='entrance_steps')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='FileEntranceExamTask',
            fields=[
                ('entranceexamtask_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, to='entrance.EntranceExamTask', serialize=False)),
            ],
            bases=('entrance.entranceexamtask',),
        ),
        migrations.CreateModel(
            name='FileEntranceExamTaskSolution',
            fields=[
                ('entranceexamtasksolution_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, to='entrance.EntranceExamTaskSolution', serialize=False)),
                ('original_filename', models.TextField()),
            ],
            bases=('entrance.entranceexamtasksolution',),
        ),
        migrations.CreateModel(
            name='ProgramEntranceExamTask',
            fields=[
                ('entranceexamtask_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, to='entrance.EntranceExamTask', serialize=False)),
                ('ejudge_contest_id', models.PositiveIntegerField(help_text='ID контеста в еджадже')),
                ('ejudge_problem_id', models.PositiveIntegerField(help_text='ID задачи в еджадже')),
            ],
            bases=('entrance.entranceexamtask',),
        ),
        migrations.CreateModel(
            name='ProgramEntranceExamTaskSolution',
            fields=[
                ('entranceexamtasksolution_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, to='entrance.EntranceExamTaskSolution', serialize=False)),
                ('ejudge_queue_element', models.ForeignKey(on_delete=models.CASCADE, to='ejudge.QueueElement')),
                ('language', models.ForeignKey(on_delete=models.CASCADE, to='ejudge.ProgrammingLanguage')),
            ],
            bases=('entrance.entranceexamtasksolution',),
        ),
        migrations.CreateModel(
            name='TestEntranceExamTask',
            fields=[
                ('entranceexamtask_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, to='entrance.EntranceExamTask', serialize=False)),
                ('correct_answer_re', models.CharField(max_length=100, help_text='Правильный ответ (регулярное выражение)')),
                ('validation_re', models.CharField(blank=True, max_length=100, help_text='Регулярное выражение для валидации ввода')),
            ],
            bases=('entrance.entranceexamtask',),
        ),
        migrations.AddField(
            model_name='entrancelevel',
            name='tasks',
            field=models.ManyToManyField(to='entrance.EntranceExamTask', blank=True),
        ),
        migrations.AddField(
            model_name='entranceexamtasksolution',
            name='task',
            field=models.ForeignKey(on_delete=models.CASCADE, to='entrance.EntranceExamTask'),
        ),
        migrations.AddField(
            model_name='entranceexamtasksolution',
            name='user',
            field=models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entranceexamtask',
            name='exam',
            field=models.ForeignKey(on_delete=models.CASCADE, to='entrance.EntranceExam', related_name='entranceexamtask'),
        ),
        migrations.AlterIndexTogether(
            name='entranceexamtasksolution',
            index_together=set([('task', 'user')]),
        ),
    ]
