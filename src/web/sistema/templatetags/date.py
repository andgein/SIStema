import datetime

from django import template
from django.utils.dateformat import format
from django.conf import settings
from django.utils import formats


register = template.Library()


date_format = formats.get_format('DATE_FORMAT',
                                 lang=settings.LANGUAGE_CODE)
without_year_date_format = date_format\
    .replace('Y', '').replace('г.', '').replace('.Y', '').replace('/Y', '')\
    .strip()


@register.filter
def without_year(date, year=None):
    if year is None:
        year = datetime.datetime.now().year
    year = int(year)
    if date.year == year:
        return format(date, without_year_date_format)
    return format(date, date_format)
