from django.template import Library

register = Library()


@register.filter
def get_item(obj, key):
    try:
        return obj.__getitem__(key)
    except KeyError:
        raise KeyError("Can't get item \"%s\" from %s" % (key, obj))


@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr)
