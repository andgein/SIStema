from django.db.models import Q
import django.contrib.admin.views.decorators as admin_decorators
import django.utils.decorators as utils_decorators

from dal import autocomplete

from users import models

@utils_decorators.method_decorator(admin_decorators.staff_member_required,
                                   name='dispatch')
class UserAutocomplete(autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        super().__init__(model=models.User, **kwargs)

    def get_queryset(self):
        qs = models.User.objects.all()

        if self.q.isdigit():
            qs = qs.filter(id=int(self.q))
        elif self.q:
            for token in self.q.strip().split(' '):
                qs = qs.filter(Q(profile__first_name__icontains=token) |
                               Q(profile__middle_name__icontains=token) |
                               Q(profile__last_name__icontains=token))

        return qs
