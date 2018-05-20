from django.urls import path

from groups import views

app_name = 'groups'


urlpatterns = [
    path(
        'user_autocomplete/group/<int:group_id>/',
        views.UsersFromGroupAutocomplete.as_view(),
        name='users-from-group-autocomplete',
    ),
]
