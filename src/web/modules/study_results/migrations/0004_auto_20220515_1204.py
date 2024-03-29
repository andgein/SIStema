# Generated by Django 3.2.13 on 2022-05-15 12:04

from django.db import migrations, models
import djchoices.choices


class Migration(migrations.Migration):

    dependencies = [
        ('study_results', '0003_auto_20211229_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studyresult',
            name='practice',
            field=models.CharField(choices=[('N/A', 'N/A'), ('2', '2'), ('2+', '2+'), ('3-', '3-'), ('3', '3'), ('3+', '3+'), ('4-', '4-'), ('4', '4'), ('4+', '4+'), ('5-', '5-'), ('5', '5'), ('5+', '5+')], max_length=3, null=True, validators=[djchoices.choices.ChoicesValidator({'2': '2', '2+': '2+', '3': '3', '3+': '3+', '3-': '3-', '4': '4', '4+': '4+', '4-': '4-', '5': '5', '5+': '5+', '5-': '5-', 'N/A': 'N/A'})]),
        ),
        migrations.AlterField(
            model_name='studyresult',
            name='theory',
            field=models.CharField(choices=[('N/A', 'N/A'), ('2', '2'), ('2+', '2+'), ('3-', '3-'), ('3', '3'), ('3+', '3+'), ('4-', '4-'), ('4', '4'), ('4+', '4+'), ('5-', '5-'), ('5', '5'), ('5+', '5+')], max_length=3, null=True, validators=[djchoices.choices.ChoicesValidator({'2': '2', '2+': '2+', '3': '3', '3+': '3+', '3-': '3-', '4': '4', '4+': '4+', '4-': '4-', '5': '5', '5+': '5+', '5-': '5-', 'N/A': 'N/A'})]),
        ),
    ]
