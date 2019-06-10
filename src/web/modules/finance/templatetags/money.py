from django.template import Library

from modules.finance.models.currency import Currency
from sistema.templatetags.number_to_text import pluralize

register = Library()


@register.filter(is_safe=False)
def money_russian_pluralize(amount, currency):
    """
    Returns "5 рублей" or "2 доллара"
    """
    forms = {
        Currency.RUB: ('рубль', 'рубля', 'рублей'),
        Currency.EUR: ('евро', 'евро', 'евро'),
        Currency.USD: ('доллар', 'доллара', 'долларов'),
    }
    return str(amount) + ' ' + pluralize(amount, *forms[currency])
