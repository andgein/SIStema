from modules.poldnev import models
from django.db.models import Q


__all__ = ['filter_persons']


_no_break_space = b'\xc2\xa0'.decode('utf8')


def _normalize(s):
    s = s.lower()
    """ Last name 'Деб Натх' contains no-break space instead of space"""
    s = s.replace(_no_break_space, ' ')
    return s


def filter_persons(query, *, queryset=None):
    """
    Filter persons by query.

    :param query: Query string. Should consist of space-separated tokens.
    :param queryset: QuerySet of poldnev.Person to filter. If not provided all
        the persons are searched.
    :return: Filtered QuerySet
    """
    if queryset is None:
        queryset = models.Person.objects.all()

    if query:
        for token in query.strip().split(' '):
            queryset = queryset.filter(
                Q(last_name__icontains=token)
                | Q(first_name__icontains=token)
                | Q(middle_name__icontains=token))

        # Leave only full string matches
        normalized_query = _normalize(query)
        if ' ' in normalized_query:
            # TODO(artemtab): optimize this further. how?
            ids = [person.pk for person in queryset if
                   normalized_query in _normalize(person.full_name)]
            queryset = models.Person.objects.filter(pk__in=ids)

    return queryset
