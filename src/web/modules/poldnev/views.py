from dal import autocomplete

from modules.poldnev import models, search
from django.template.loader import render_to_string


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        super().__init__(model=models.Person, **kwargs)

    def get_queryset(self):
        return search.filter_persons(self.q)

    def get_result_label(self, item):
        return render_to_string('poldnev/_person_select_item.html', {
            'person': item
        })
