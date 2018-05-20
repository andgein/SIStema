import dal.autocomplete
from django.db.models import Q

from groups import models
import users.models


class UsersFromGroupAutocomplete(dal.autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        self.group_id = None
        super().__init__(model=users.models.User, **kwargs)

    def dispatch(self, request, group_id, *args, **kwargs):
        self.group_id = group_id
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        group = (
            models.AbstractGroup.objects
            .filter(id=self.group_id)
            .first())
        if group is None:
            return users.models.User.objects.none()

        # Check whether current user can see a list of group members
        access_type = group.get_access_type_for_user(self.request.user)
        if access_type < models.GroupAccess.Type.LIST_MEMBERS:
            return users.models.User.objects.none()

        qs = group.users.order_by('profile__last_name', 'profile__first_name')
        if self.q:
            for token in self.q.strip().split(' '):
                qs = qs.filter(
                    Q(profile__last_name__icontains=token) |
                    Q(profile__first_name__icontains=token))
        return qs

    def get_result_label(self, item):
        return '{} {}'.format(item.profile.last_name, item.profile.first_name)
