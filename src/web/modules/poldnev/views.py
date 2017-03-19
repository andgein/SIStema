from dal import autocomplete

from modules.poldnev import models
from django.template.loader import render_to_string
from django.db.models import Q

_no_break_space = b'\xc2\xa0'.decode('utf8')


def _normalize(s):
    s = s.lower()
    """ Last name 'Деб Натх' contains no-break space instead of space"""
    s = s.replace(_no_break_space, ' ')
    return s


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        super().__init__(model=models.Person, **kwargs)

    def get_queryset(self):
        qs = models.Person.objects.all()
        if self.q:
            for token in self.q.strip().split(' '):
                qs = qs.filter(Q(last_name__icontains=token)
                               | Q(first_name__icontains=token)
                               | Q(middle_name__icontains=token))
            norm_query = _normalize(self.q)
            # TODO optimize this. how?
            ids = [person.pk for person in qs if norm_query in _normalize(person.full_name)]
            qs = models.Person.objects.filter(pk__in=ids)

        return qs

    def get_result_label(self, item):
        return render_to_string('poldnev/_person_select_item.html', {
            'person': item
        })
