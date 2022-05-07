from functools import wraps

from django.db.models import Q
from django.http.response import HttpResponseNotFound

from groups.models import AbstractGroup

__all__ = ['only_for_groups']


def only_for_groups(*group_names):
    """
    This decorator passes the request further if (and only if)
    user is a member of at least one of groups specified in `group_names`.
    Groups should be created in the school from the request (`request.school`)
    or as system-wide.
    Otherwise, decorator returns HttpResponseNotFound()
    :param group_names: list of group's short_names
    """
    if len(group_names) == 0:
        raise ValueError(
            '@only_for_groups() should be used with group names as arguments'
        )

    def decorator(handler):
        @wraps(handler)
        def func_wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseNotFound()

            if request.user.is_superuser:
                return handler(request, *args, **kwargs)

            school = getattr(request, 'school', None)

            matched_groups = AbstractGroup.objects.filter(
                Q(short_name__in=group_names) &
                (Q(school=school) | Q(school__isnull=True))
            )
            groups_by_short_name = {}
            for group in matched_groups:
                groups_by_short_name[group.short_name] = group

            # At first check all names for existing
            for group_name in group_names:
                if group_name not in groups_by_short_name:
                    raise ValueError(
                        'Invalid group_name in only_for_groups(): %s. '
                        'Can\'t find this group for school %s or system-wide' % (
                            group_name,
                            school
                        ))

            for group_name in group_names:
                group = groups_by_short_name[group_name]
                if group.is_user_in_group(request.user):
                    return handler(request, *args, **kwargs)

            return HttpResponseNotFound()
        return func_wrapper
    return decorator

