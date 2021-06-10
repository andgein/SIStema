# Generated by Django 2.2.10 on 2021-05-09 10:12
import sys

from django.db import migrations


def make_key_dates(apps, _schema_editor):
    EntranceExam = apps.get_model('entrance', 'EntranceExam')
    KeyDate = apps.get_model('dates', 'KeyDate')
    for exam in EntranceExam.objects.all():
        if exam.close_time is not None:
            exam.close_date = KeyDate.objects.create(
                datetime=exam.close_time,
                school=exam.school,
                short_name=exam.school.short_name + "_exam_end_auto_created",
                name='Окончание вступительной работы для "{}" [авто-создано, удалить при возможности]'.format(exam.school.name),
            )
            exam.save()


def make_key_dates_reverse(apps, _schema_editor):
    EntranceExam = apps.get_model('entrance', 'EntranceExam')
    for exam in EntranceExam.objects.all():
        if exam.close_date is not None:
            exam.close_time = exam.close_date.datetime
            exam.save()


def create_limiters(apps, _schema_editor):
    School = apps.get_model('schools', 'School')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    limiter_models = [
        apps.get_model('entrance', 'AlreadyWasEntranceLevelLimiter'),
        apps.get_model('entrance', 'AgeEntranceLevelLimiter'),
        apps.get_model('entrance', 'EnrollmentTypeEntranceLevelLimiter'),
    ]
    for school in School.objects.all():
        if not hasattr(school, 'entrance_exam'):
            continue
        for limiter_model in limiter_models:
            content_type = ContentType.objects.get_for_model(limiter_model)
            limiter_model.objects.get_or_create(school=school, polymorphic_ctype=content_type)


def create_already_was_limits(apps, _schema_editor):
    School = apps.get_model('schools', 'School')
    EntranceLevel = apps.get_model('entrance', 'EntranceLevel')
    AlreadyWasEntranceLevelLimiter = apps.get_model('entrance', 'AlreadyWasEntranceLevelLimiter')
    AlreadyWasEntranceLevelLimiterForParallel = apps.get_model('entrance', 'AlreadyWasEntranceLevelLimiterForParallel')

    limit_for_parallel = {
        'a': 'a',
        'a0': 'a',
        'a_ml': 'a',
        'a_prime': 'a',
        'aa': 'a',
        'as': 'a',
        'ay': 'a',
        'b': 'a_prime',
        'b_prime': 'b',
        'c': 'b_prime',
        'c.cpp': 'b_prime',
        'c.python': 'b_prime',
        'c_prime': 'c',
        'd': 'c_prime',
    }

    for school in School.objects.all():
        limiter = AlreadyWasEntranceLevelLimiter.objects.filter(school=school).first()
        if limiter is None:
            continue

        for previous_parallel, entrance_level_short_name in limit_for_parallel.items():
            level = EntranceLevel.objects.filter(school=school, short_name=entrance_level_short_name).first()
            if level is None:
                print("Level {} not found for school {}".format(entrance_level_short_name, school.name), file=sys.stderr)
                continue
            AlreadyWasEntranceLevelLimiterForParallel.objects.get_or_create(
                limiter=limiter,
                previous_parallel_short_name=previous_parallel,
                level=level
            )


def create_age_limits(apps, _schema_editor):
    School = apps.get_model('schools', 'School')
    EntranceLevel = apps.get_model('entrance', 'EntranceLevel')
    AgeEntranceLevelLimiter = apps.get_model('entrance', 'AgeEntranceLevelLimiter')
    AgeEntranceLevelLimiterForClass = apps.get_model('entrance', 'AgeEntranceLevelLimiterForClass')

    limit_for_class = {
        10: 'b_prime',
        9: 'c',
        8: 'c_prime',
    }

    for school in School.objects.all():
        limiter = AgeEntranceLevelLimiter.objects.filter(school=school).first()
        if limiter is None:
            continue

        for current_class, entrance_level_short_name in limit_for_class.items():
            level = EntranceLevel.objects.filter(school=school, short_name=entrance_level_short_name).first()
            if level is None:
                print("Level {} not found for school {}".format(entrance_level_short_name, school.name), file=sys.stderr)
                continue
            AgeEntranceLevelLimiterForClass.objects.get_or_create(
                limiter=limiter,
                current_class=current_class,
                level=level
            )


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('schools', '0018_auto_20180407_1742'),
        ('dates', '0008_auto_20180510_2140'),
        ('entrance', '0086_auto_20210509_1012'),
    ]

    operations = [
        migrations.RunPython(
            code=make_key_dates,
            reverse_code=make_key_dates_reverse,
        ),
        migrations.RunPython(
            code=create_limiters,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=create_already_was_limits,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=create_age_limits,
            reverse_code=migrations.RunPython.noop,
        ),
    ]