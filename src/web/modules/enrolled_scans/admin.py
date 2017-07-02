from django.contrib import admin

from polymorphic.admin import (StackedPolymorphicInline,
                               PolymorphicInlineSupportMixin)

import modules.entrance.admin
import sistema.admin

from . import models


class EnrolledScanRequirementConditionInline(StackedPolymorphicInline):
    class QuestionnaireVariantEnrolledScanRequirementConditionInline(
            StackedPolymorphicInline.Child
    ):
        model = models.QuestionnaireVariantEnrolledScanRequirementCondition

    model = models.EnrolledScanRequirementCondition
    child_inlines = (
        QuestionnaireVariantEnrolledScanRequirementConditionInline,
    )


@admin.register(models.EnrolledScanRequirement)
class EnrolledScanRequirementAdmin(PolymorphicInlineSupportMixin,
                                   admin.ModelAdmin):
    list_display = ('id', 'school', 'name')
    list_filter = ('school', )
    inlines = (EnrolledScanRequirementConditionInline,)


@admin.register(models.EnrolledScan)
class EnrolledScanAdmin(sistema.admin.ModelAdmin):
    list_display = ('id', 'requirement', 'user')
    list_filter = ('requirement__school', 'requirement')


admin.site.register(models.EnrolledScansEntranceStep,
                    modules.entrance.admin.EntranceStepChildAdmin)
