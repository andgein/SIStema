from django.conf.urls import url

from modules.poldnev import views

app_name = 'poldnev'


urlpatterns = [
    url(
        'person-autocomplete/$',
        views.PersonAutocomplete.as_view(),
        name='person-autocomplete',
    ),
]
