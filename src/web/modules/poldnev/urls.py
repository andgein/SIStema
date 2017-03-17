from django.conf.urls import url

from modules.poldnev import views


urlpatterns = [
    url(
        'person-autocomplete/$',
        views.PersonAutocomplete.as_view(),
        name='person-autocomplete',
    ),
]
