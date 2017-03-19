from django.template import Library

register = Library()


def _mask_str(s):
    return '%s***%s' % (s[0], s[-1])


@register.filter
def masked_email(email):
    if not email:
        return ''
    name, domain = email.lower().split('@', 2)
    domain1, domain2 = domain.lower().rsplit('.', 2)
    name = _mask_str(name)
    if domain1 not in ['gmail', 'yandex', 'ya', 'rambler', 'mail', 'yahoo']:
        domain1 = _mask_str(domain1)
    return "%s@%s.%s" % (name, domain1, domain2)
