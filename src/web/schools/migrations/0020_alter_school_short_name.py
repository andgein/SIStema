# Generated by Django 3.2.13 on 2022-05-27 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0019_auto_20211229_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='short_name',
            field=models.CharField(db_index=True, help_text='Используется в урлах. Например, 2048', max_length=20, unique=True),
        ),
    ]
