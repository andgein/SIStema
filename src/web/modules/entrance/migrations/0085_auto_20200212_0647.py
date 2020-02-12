# Generated by Django 2.2.10 on 2020-02-12 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0084_selectedenrollmenttypegroup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstractentrancestep',
            name='visible_only_for_enrolled',
            field=models.BooleanField(blank=True, default=False, help_text='Шаг будет виден только зачисленным в школу пользователям'),
        ),
    ]
