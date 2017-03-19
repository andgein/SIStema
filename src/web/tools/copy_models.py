"""
Example usage:
>>> from tools.copy_models import copy_models
>>> import schools.models
>>> from modules.topics import models
>>> sis2016 = schools.models.School.objects.get(short_name='2016')
>>> sis2017 = schools.models.School.objects.get(short_name='2017')
>>> copy_models(sis2016, sis2017, [models.LevelUpwardDependency,
...                                models.LevelDownwardDependency])
"""

import collections

import schools.models

def copy_models(from_school, to_school, models):
    """
    Copy instances of classes listed in models from from_school to to_school.
    """

    for model_cls in models:
        copy_model_objects(from_school, to_school, model_cls)


def copy_model_objects(from_school, to_school, model_cls):
    """
    Copy instances of model_cls from from_school to to_school. Also copy
    instances of foreign keys if they depend on school.
    """

    for obj in model_cls.objects.all():
        if get_school(obj) == from_school:
            copy_object(from_school, to_school, obj)


def copy_object(from_school, to_school, obj):
    """
    Copy object replacing from_school with to_school if:
    - It depends on from_school, maybe indirectly
    - It's not yet copied

    Return the copied object or original one if copy is not needed
    """

    if get_school(obj) != from_school:
        return obj

    if obj == from_school:
        return to_school

    cls = obj.__class__

    all_fields = cls._meta.get_fields()
    own_fields = [f for f in all_fields if not is_related_field(f)]
    plain_fields = [f for f in own_fields
                    if is_plain_field(f) and f.name != cls._meta.pk.attname]
    relation_fields = [f for f in own_fields if not is_plain_field(f)]
    to_one_fields = [f for f in relation_fields
                     if f.one_to_one or f.many_to_one]
    many_to_many_fields = [f for f in relation_fields if f.many_to_many]

    # Arguments for object creation
    kwargs = {}

    # Copy plain fields
    for f in plain_fields:
        kwargs[f.name] = getattr(obj, f.name)

    # Deep copy foreign keys and one to one fields
    for f in to_one_fields:
        kwargs[f.name] = copy_object(
            from_school, to_school, getattr(obj, f.name))

    # If the object for new school already exists, just return it
    if cls.objects.filter(**kwargs).exists():
        new_obj = cls.objects.get(**kwargs)
        return new_obj

    # Deep copy many to many fields
    many_to_many_values = collections.defaultdict(list)
    for f in many_to_many_fields:
        for rel_obj in getattr(obj, f.name).all():
            many_to_many_values[f.name].append(
                copy_object(from_school, to_school, rel_obj)
            )

    new_obj = cls.objects.create(**kwargs)
    for key, values in many_to_many_values.items():
        getattr(new_obj, key).add(*values)

    print('Copied {} to {}'.format(obj, new_obj))

    return new_obj


def get_school(obj, cache={}):
    """
    Return None if obj is associated (maybe indirectly) with no school or with
    many schools.

    Return schools.models.School object if obj is associated with a signle
    school.
    """
    key = '{}:{}'.format(obj.__class__.__name__, obj.id)

    if key not in cache:
        if isinstance(obj, schools.models.School):
            cache[key] = obj
        else:
            objects_to_check = []
            for field in obj.__class__._meta.get_fields():
                # Ignore plain and related fields
                if is_plain_field(field) or is_related_field(field):
                    continue

                if field.many_to_one or field.one_to_one:
                    objects_to_check.append(getattr(obj, field.name))
                elif field.many_to_many:
                    objects_to_check.extend(getattr(obj, field.name).all())
                else:
                    raise TypeError('Unknown field type')

            associated_schools = set(get_school(next_obj)
                                     for next_obj in objects_to_check)

            if len(associated_schools) == 1:
                cache[key] = associated_schools.pop()
            else:
                cache[key] = None

    return cache[key]


def is_plain_field(field):
    return (not field.one_to_one and not field.one_to_many and
            not field.many_to_one and not field.many_to_many)


# TODO: Check that it's true
def is_related_field(field):
    """
    Returns true if the field created as a related field from another model.
    """
    return hasattr(field, 'related_name')
