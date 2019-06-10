# -*- coding: utf-8 -*-

from django.db import models

from .discount import Discount
from .currency import Currency

import schools.models
import users.models


class PaymentAmount(models.Model):
    school = models.ForeignKey(
        schools.models.School,
        on_delete=models.CASCADE,
        related_name='+',
    )

    user = models.ForeignKey(
        users.models.User,
        on_delete=models.CASCADE,
        related_name='+',
    )

    amount = models.PositiveIntegerField(help_text='Сумма к оплате')

    currency = models.PositiveIntegerField(choices=Currency.choices, validators=[Currency.validator])

    class Meta:
        unique_together = ('school', 'user')

    @classmethod
    def get_amount_for_user(cls, school, user):
        """
        Returns (amount, currency)
        """
        amount_object = cls.objects.filter(school=school, user=user).first()
        if amount_object is None:
            return None, None
        amount = amount_object.amount

        discounts = (Discount.objects
                             .filter(school=school, user=user)
                             .values_list('amount', flat=True))

        max_discount = max(discounts, default=0)

        amount -= max_discount
        if amount < 0:
            amount = 0

        return amount, amount_object.currency
