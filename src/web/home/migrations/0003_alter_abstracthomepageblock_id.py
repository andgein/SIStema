# Generated by Django 3.2.10 on 2021-12-29 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_auto_20180217_0000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstracthomepageblock',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
