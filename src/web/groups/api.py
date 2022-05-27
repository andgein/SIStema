def is_user_in_group(user, group_name, school=None):
    """
    Check whether the user is in the group
    :param user: User object
    :param group_name: group's short_name
    :param school: if school is None, look only for a system-wide group.
    Otherwise look for a group belonging to this school
    :return: True if user is in group, False otherwise
    """
    # Importing here because this API is pulled into __init__.py. Django is unable to load models there.
    from groups import models

    group = models.AbstractGroup.objects.filter(
        school=school, short_name=group_name
    ).select_related('school').first()
    if group is None:
        raise ValueError('Unknown group name %s for school %s' % (
            group_name,
            school
        ))

    return group.is_user_in_group(user)
