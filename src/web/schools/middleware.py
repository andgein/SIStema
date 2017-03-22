from django import shortcuts, http
from schools import models as school_models


class SchoolMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'school_name' in view_kwargs:
            request.school = shortcuts.get_object_or_404(
                school_models.School,
                short_name=view_kwargs['school_name']
            )
            del view_kwargs['school_name']
            school = request.school
            user = request.user
            if not school.is_public and not (user.is_authenticated and user.is_staff):
                return http.HttpResponseNotFound()
        return None
