import djchoices


class Currency(djchoices.DjangoChoices):
    RUB = djchoices.ChoiceItem(value=0, label='Рубли')

    EUR = djchoices.ChoiceItem(value=1, label='Евро')

    USD = djchoices.ChoiceItem(value=2, label='Доллар')
