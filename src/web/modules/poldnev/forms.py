from dal import autocomplete

from django import forms

from modules.poldnev import models
from django.template.loader import render_to_string


class PersonField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super().__init__(queryset=models.Person.objects.all(),
                         widget=autocomplete.ModelSelect2(
                             url='poldnev:person-autocomplete',
                             attrs={
                                 'data-placeholder': 'Начните вводить фамилию',
                                 'data-html': 'true',
                             },
                         ),
                         *args, **kwargs)

    def label_from_instance(self, obj):
        return render_to_string('poldnev/_person_select_item.html', {'person': obj})
