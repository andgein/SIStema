from django.template import Library

register = Library()


hundreds = [
    '',
    'сто',
    'двести',
    'триста',
    'четыреста',
    'пятьсот',
    'шестьсот',
    'семьсот',
    'восемьсот',
    'девятьсот'
]

first_decade = [
    '',
    ('одна', 'один'),
    ('две', 'два'),
    'три',
    'четыре',
    'пять',
    'шесть',
    'семь',
    'восемь',
    'девять'
]

second_decade = [
    'десять',
    'одиннадцать',
    'двенадцать',
    'тринадцать',
    'четырнадцать',
    'пятнадцать',
    'шестнадцать',
    'семнадцать',
    'восемнадцать',
    'девятнадцать'
]

decades = [
    '',
    'десять',
    'двадцать',
    'тридцать',
    'сорок',
    'пятьдесят',
    'шестьдесят',
    'семьдесят',
    'восемьдесят',
    'девяносто'
]


def pluralize(number, one, two, five):
    last_digit = number % 10
    prelast_digit = (number // 10) % 10
    if last_digit == 1 and prelast_digit != 1:
        return one
    if 2 <= last_digit <= 4 and prelast_digit != 1:
        return two
    return five


@register.filter(is_safe=False)
def russian_pluralize(value, arg='s'):
    if ',' not in arg:
        arg = ',' + arg
    bits = arg.split(',')
    if len(bits) > 3:
        return ''
    one, two, five = bits[:3]
    return pluralize(value, one, two, five)


@register.filter
def number_to_text(number, gender='male', return_text_for_zero=True):
    """ Supports numbers less than 1 000 000 000 """

    if number is None or number == 0:
        return 'ноль' if return_text_for_zero else ''

    text = []
    if number >= 1000000:
        billions = number // 1000000
        text.extend([number_to_text(billions, gender='male', return_text_for_zero=False),
                     'миллион' + pluralize(billions, '', 'а', 'ов')])
        number %= 100000

    if number >= 1000:
        thousands = number // 1000
        text.extend([number_to_text(thousands, gender='female', return_text_for_zero=False),
                     'тысяч' + pluralize(thousands, 'а', 'и', '')])
        number %= 1000

    if number >= 100:
        text.append(hundreds[number // 100])
        number %= 100

    if number == 0:
        pass
    elif number < 10:
        number_text = first_decade[number]
        if isinstance(number_text, (tuple, list)):
            number_text = number_text[1 if gender == 'male' else 0]
        text.append(number_text)
    elif number < 20:
        text.append(second_decade[number - 10])
    else:
        number_text = first_decade[number % 10]
        if isinstance(number_text, (tuple, list)):
            number_text = number_text[1 if gender == 'male' else 0]
        text.extend([decades[number // 10], number_text])

    return ' '.join(text)


