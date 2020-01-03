# Generated by Django 2.0.3 on 2020-01-03 12:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('polygon', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('polygon_id', models.IntegerField(help_text='ID контеста в полигоне', primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, help_text='Имя контеста в полигоне', max_length=300, verbose_name='name')),
            ],
            options={
                'verbose_name': 'contest',
                'verbose_name_plural': 'contests',
            },
        ),
        migrations.CreateModel(
            name='ProblemInContest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.CharField(help_text='Индекс задачи в контесте (например, A, B, C, ...)', max_length=32, verbose_name='index')),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problem_entries', to='polygon.Contest', verbose_name='contest')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contest_entries', to='polygon.Problem', verbose_name='problem')),
            ],
            options={
                'verbose_name': 'problem in contest',
                'verbose_name_plural': 'problem in contests',
            },
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'verbose_name': 'tag', 'verbose_name_plural': 'tags'},
        ),
        migrations.AlterUniqueTogether(
            name='problemincontest',
            unique_together={('contest', 'problem')},
        ),
    ]
