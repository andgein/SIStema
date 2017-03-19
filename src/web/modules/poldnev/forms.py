from django import forms
from django.template.loader import render_to_string

import frontend.forms
from modules.poldnev import models


class PersonField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(queryset=models.Person.objects.all(),
                         widget=frontend.forms.ModelAutocompleteSelect2(
                             url='poldnev:person-autocomplete',
                             attrs={
                                 'data-placeholder': 'Выберите себя из списка',
                                 'data-html': 'true',
                             },
                         ),
                         *args, **kwargs)

    def label_from_instance(self, obj):
        return render_to_string('poldnev/_person_select_item.html', {
            'person': obj
        })
