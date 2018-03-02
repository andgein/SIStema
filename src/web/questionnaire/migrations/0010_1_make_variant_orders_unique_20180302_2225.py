import operator

from django.db import migrations

from sistema.helpers import group_by


def make_quesetion_variant_orders_unique(apps, schema):
    Variant = apps.get_model(
        'questionnaire', 'ChoiceQuestionnaireQuestionVariant')

    variants = Variant.objects.prefetch_related('question')
    variants_by_question = group_by(variants, operator.attrgetter('question'))
    for question_variants in variants_by_question.values():
        question_variants.sort(key=operator.attrgetter('order'))
        order = 10
        for variant in question_variants:
            variant.order = order
            variant.save()
            order += 10


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0009_auto_20180225_2031'),
    ]

    operations = [
        migrations.RunPython(
            make_quesetion_variant_orders_unique, migrations.RunPython.noop),
    ]
