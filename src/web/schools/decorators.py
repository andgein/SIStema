from django import shortcuts
from django.shortcuts import redirect

from .models import *


# TODO(Artem Tabolin): move the definition of school_name argument from
#     sistema.urls to schools.url. The dependency on sistema app is not required
#     here, so it should be removed.
def school_view(view):
    def func_wrapper(request, school_name, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('home')

        request.school = shortcuts.get_object_or_404(School,
                                                     short_name=school_name)
        if request.school.is_public or request.user.is_staff:
            return view(request, *args, **kwargs)
        return redirect('home')

    func_wrapper.__doc__ = view.__doc__
    func_wrapper.__name__ = view.__name__
    func_wrapper.__module__ = view.__module__
    return func_wrapper
