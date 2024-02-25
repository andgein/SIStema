from django.urls import path

from modules.poldnev import views

app_name = 'poldnev'


urlpatterns = [
    path('person-autocomplete/', views.PersonAutocomplete.as_view(), name='person-autocomplete'),
]
