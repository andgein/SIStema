from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelFilter

from home import models
import sistema.polymorphic


@admin.register(models.AbstractHomePageBlock)
class AbstractHomePageBlockAdmin(
        sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractHomePageBlock
    list_display = ('id', 'school', 'order')
    list_filter = ('school', PolymorphicChildModelFilter)
    search_field = ('=id',)
    ordering = ('-school', 'order')
