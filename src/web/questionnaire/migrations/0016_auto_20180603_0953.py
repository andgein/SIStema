# Generated by Django 2.0.3 on 2018-06-03 04:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0015_auto_20180602_2026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='questionnaireblockgroupmembershowcondition',
            old_name='need_to_be_member',
            new_name='group',
        ),
        migrations.RenameField(
            model_name='questionnaireblockvariantcheckedshowcondition',
            old_name='need_to_be_checked',
            new_name='variant',
        ),
    ]
