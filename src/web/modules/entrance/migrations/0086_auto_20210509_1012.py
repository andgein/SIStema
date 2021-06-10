# Generated by Django 2.2.10 on 2021-05-09 10:12
import sys

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('schools', '0018_auto_20180407_1742'),
        ('dates', '0008_auto_20180510_2140'),
        ('entrance', '0085_auto_20200212_0647'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntranceLevelLimiter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_entrance.entrancelevellimiter_set+', to='contenttypes.ContentType')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entrance_level_limiters', to='schools.School')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.AddField(
            model_name='entranceexam',
            name='can_participant_select_entrance_level',
            field=models.BooleanField(default=False, help_text='Может ли школьник выбрать себе уровень вступительной работы. Если True, тошкольнику будет предоставлен выбор, начиная с минимального уровня, на который он может претендовать. Если False, то уровень выдаётся автоматически на основе тематической анкеты и других параметров. При решении определённых задач школьник может поднять себе уровень.'),
        ),
        migrations.AddField(
            model_name='entranceexam',
            name='close_date',
            field=models.ForeignKey(blank=True, default=None, help_text='Время окончания экзамена', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='dates.KeyDate'),
        ),
        migrations.CreateModel(
            name='AgeEntranceLevelLimiter',
            fields=[
                ('entrancelevellimiter_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='entrance.EntranceLevelLimiter')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('entrance.entrancelevellimiter',),
        ),
        migrations.CreateModel(
            name='AlreadyWasEntranceLevelLimiter',
            fields=[
                ('entrancelevellimiter_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='entrance.EntranceLevelLimiter')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('entrance.entrancelevellimiter',),
        ),
        migrations.CreateModel(
            name='EnrollmentTypeEntranceLevelLimiter',
            fields=[
                ('entrancelevellimiter_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='entrance.EntranceLevelLimiter')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('entrance.entrancelevellimiter',),
        ),
        migrations.CreateModel(
            name='AgeEntranceLevelLimiterForClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_class', models.IntegerField(help_text='Текущий класс школьника (например, если тут указан 8 класс, то уровень будет применяться как ограничения для всех, кто в 8 классе и старше)')),
                ('level', models.ForeignKey(help_text='Какой уровень вступительной для такого школьника будет минимальным', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='entrance.EntranceLevel')),
                ('limiter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='limits_for_classes', to='entrance.AgeEntranceLevelLimiter')),
            ],
        ),
        migrations.CreateModel(
            name='AlreadyWasEntranceLevelLimiterForParallel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_parallel_short_name', models.CharField(blank=True, default='', help_text='short_name параллели, в которой был школьник. Укажите это поле или previous_parallel.', max_length=100)),
                ('level', models.ForeignKey(help_text='Какой уровень вступительной для такого школьника будет минимальным', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='entrance.EntranceLevel')),
                ('previous_parallel', models.ForeignKey(blank=True, default=None, help_text='Параллель, в которой был школьник. Укажите это поле или previous_parallel_short_name', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='schools.Parallel')),
                ('limiter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='limits_for_parallels', to='entrance.AlreadyWasEntranceLevelLimiter')),
            ],
            options={
                'unique_together': {('limiter', 'previous_parallel')},
            },
        ),
    ]