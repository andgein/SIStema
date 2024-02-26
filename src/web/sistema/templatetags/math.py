from django import template

register = template.Library()


@register.filter
def divide(value, arg):
    """
    Divides the value; argument is the divisor.
    Returns empty string on any error.
    """
    try:
        value = int(value)
        arg = int(arg)
        if arg:
            return value / arg
    except (ValueError, TypeError, ArithmeticError):
        return ''
    return ''


@register.filter
def multiply(value, arg):
    """
    Multiple values.
    Returns empty string on any error.
    """
    try:
        value = int(value)
        arg = int(arg)
        return value * arg
    except (ValueError, TypeError):
        return ''


@register.filter
def add(value, arg):
    """ Sum values """
    return value + arg


@register.filter
def subtract(value, arg):
    """ Subtract values """
    return value - arg


@register.filter
def to_int(value):
    """
    Converting any value to int.
    Returns empty string on any error.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return ''
