# Generated by Django 2.0.3 on 2018-04-06 11:46

from django.db import migrations


def create_default_categories(apps, schema):
    exam_class = apps.get_model('entrance', 'EntranceExam')
    task_class = apps.get_model('entrance', 'EntranceExamTask')
    task_category_class = apps.get_model('entrance', 'EntranceExamTaskCategory')
    for exam in exam_class.objects.all():
        tasks = task_class.objects.filter(exam=exam)
        types = {task.polymorphic_ctype.model for task in tasks}
        short_name_for_model = create_categories_for_types(
            types=types,
            exam=exam,
            category_class=task_category_class)
        for task in tasks:
            short_name = short_name_for_model[task.polymorphic_ctype.model]
            task.category = exam.task_categories.get(short_name=short_name)
            task.save()


def create_categories_for_types(types, exam, category_class):
    params_for_type = {
        'testentranceexamtask': {
            'title': 'Тестовые задания',
            'short_name': 'test',
            'order': 10,
        },
        'fileentranceexamtask': {
            'title': 'Теоретические задачи',
            'short_name': 'theory',
            'order': 20,
        },
        'programentranceexamtask': {
            'title': 'Практические задачи',
            'short_name': 'practice',
            'order': 30
        },
        'outputonlyentranceexamtask': {
            'title': 'Практические задачи',
            'short_name': 'practice',
            'order': 30
        },
    }
    fallback_order = 40
    fallback_short_name_id = 1
    short_name_for_model = {}
    for model in types:
        params = params_for_type.get(model)
        if params is None:
            params = {
                'title': 'Задачи',
                'short_name': 'category-' + str(fallback_short_name_id),
                'order': fallback_order,
            }
            fallback_order += 10
            fallback_short_name_id += 1
        category_class.objects.get_or_create(
            exam=exam,
            **params,
        )
        short_name_for_model[model] = params['short_name']
    return short_name_for_model


class Migration(migrations.Migration):

    dependencies = [
        ('entrance', '0067_2_add_category_to_task_20180406_1146'),
    ]

    operations = [
        migrations.RunPython(
            create_default_categories, migrations.RunPython.noop)
    ]
