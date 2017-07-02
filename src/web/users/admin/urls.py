from django.conf.urls import url

from users.admin import views


urlpatterns = [
    url(r'^user-autocomplete/$',
        views.UserAutocomplete.as_view(),
        name='user-autocomplete'),
]
