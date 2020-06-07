import functools

from django.shortcuts import redirect
from django.urls import reverse

_registered_staff_interfaces = []


class MenuItem:
    def __init__(self, request, text, view_name, icon, label=None, button=None, child=None):
        if isinstance(view_name, tuple) and len(view_name) == 2:
            view_name, view_params = view_name
        else:
            view_params = {}

        if hasattr(request, 'school') and 'school_name' not in view_params:
            view_params['school_name'] = request.school.short_name

        self.text = text
        if view_name == '':
            self.view_link = '#'
        else:
            self.view_link = reverse(view_name, kwargs=view_params)
        self.view_params = view_params
        self.icon = icon
        self.label = label
        self.button = button
        self.child = child


class MenuItemLabel:
    def __init__(self, text, color):
        self.text = text
        self.color = color


class StaffInterface:
    def __init__(self, request):
        self.request = request

    def get_sidebar_menu(self):
        raise NotImplementedError('StaffInterface should implement get_sidebar_menu()')


def register_staff_interface(cls):
    if cls not in _registered_staff_interfaces:
        if not issubclass(cls, StaffInterface):
            raise ValueError('register_staff_interface: You need to subclass sistema.staff.StaffInterface')
        _registered_staff_interfaces.append(cls)


def get_staff_interfaces(request):
    return [cls(request) for cls in _registered_staff_interfaces]


def get_sidebar_menu(request):
    menu_items = []
    for interface in get_staff_interfaces(request):
        menu_items.extend(interface.get_sidebar_menu())
    return menu_items


def staff_context_processor(request):
    if request.user.is_authenticated:
        if request.user.is_staff and hasattr(request, 'school'):
            return {'staff_sidebar_menu': get_sidebar_menu(request)}
    return {}


# TODO(Artem Tabolin): is there any reason for not moving that function to
#     users.decorators or to .decorators?
def only_staff(func):
    @functools.wraps(func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('account_login')
        return func(request, *args, **kwargs)
    return wrapped
