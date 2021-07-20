from django.contrib import admin
from django.utils import html
from django.utils.safestring import mark_safe

from polymorphic.admin import (StackedPolymorphicInline,
                               PolymorphicInlineSupportMixin)

import modules.entrance.admin
import groups.admin
from . import models


class EnrolledScanRequirementConditionInline(StackedPolymorphicInline):
    class QuestionnaireVariantEnrolledScanRequirementConditionInline(
            StackedPolymorphicInline.Child
    ):
        model = models.QuestionnaireVariantEnrolledScanRequirementCondition
        autocomplete_fields = ('variant',)

    class GroupEnrolledScanRequirementConditionInline(
            StackedPolymorphicInline.Child
    ):
        model = models.GroupEnrolledScanRequirementCondition
        autocomplete_fields = ('group',)

    model = models.EnrolledScanRequirementCondition
    child_inlines = (
        QuestionnaireVariantEnrolledScanRequirementConditionInline,
        GroupEnrolledScanRequirementConditionInline,
    )


@admin.register(models.EnrolledScanRequirement)
class EnrolledScanRequirementAdmin(PolymorphicInlineSupportMixin,
                                   admin.ModelAdmin):
    list_display = ('id', 'school', 'name', 'get_conditions')
    list_filter = ('school', )
    inlines = (EnrolledScanRequirementConditionInline,)
    search_fields = ('school__name', 'name')

    def get_conditions(self, requirement):
        result = ''
        for condition in requirement.conditions.all():
            result += '<p>{}</p>'.format(html.escape(str(condition)))
        return mark_safe(result)

    get_conditions.short_description = 'Conditions'


@admin.register(models.EnrolledScan)
class EnrolledScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'requirement', 'user')
    list_filter = ('requirement__school', 'requirement')
    autocomplete_fields = ('requirement', 'user')


admin.site.register(models.EnrolledScansEntranceStep,
                    modules.entrance.admin.EntranceStepChildAdmin)


@admin.register(models.UploadedEnrolledScanGroup)
class UploadedEnrolledScanGroupAdmin(groups.admin.AbstractGroupAdmin):
    autocomplete_fields = (
        groups.admin.AbstractGroupAdmin.autocomplete_fields + ('requirement', )
    )
