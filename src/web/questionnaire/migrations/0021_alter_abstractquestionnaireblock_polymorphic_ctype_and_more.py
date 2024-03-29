# Generated by Django 4.0.10 on 2024-02-26 18:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('questionnaire', '0020_auto_20211229_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstractquestionnaireblock',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='questionnaireblockgroupmembershowcondition',
            name='block',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='show_conditions_%(class)s', to='questionnaire.abstractquestionnaireblock'),
        ),
        migrations.AlterField(
            model_name='questionnaireblockvariantcheckedshowcondition',
            name='block',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='show_conditions_%(class)s', to='questionnaire.abstractquestionnaireblock'),
        ),
    ]
