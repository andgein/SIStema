# Generated by Django 3.2.10 on 2021-12-29 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrolled_scans', '0010_uploadedenrolledscangroup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enrolledscan',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='enrolledscanrequirement',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='enrolledscanrequirementcondition',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
