from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from modules.finance import models
import modules.entrance.admin
import modules.entrance.models
import questionnaire.models
import users.models


class PaymentAmountAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'amount')
    list_filter = ('school',)
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username')

admin.site.register(models.PaymentAmount, PaymentAmountAdmin)


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'type', 'amount', 'private_comment',
                    'public_comment')
    list_filter = ('school', 'type')
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username',
        'private_comment',
        'public_comment')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = (
                users.models.User.objects.filter(
                    entrance_statuses__status=modules.entrance.models.EntranceStatus.Status.ENROLLED
                ).distinct().order_by(
                    'profile__last_name',
                    'profile__first_name'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(models.Discount, DiscountAdmin)


@admin.register(models.PaymentInfoQuestionnaireBlock)
class PaymentInfoQuestionnaireBlockAdmin(PolymorphicChildModelAdmin):
    base_model = questionnaire.models.AbstractQuestionnaireBlock


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'short_name', 'name')
    list_display_links = ('id', 'short_name')
    search_fields = ('short_name', 'name')
    list_filter = ('school', )

admin.site.register(models.DocumentType, DocumentTypeAdmin)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'type', '_users_list', 'created_at')
    search_fields = (
        'users__profile__first_name',
        'users__profile__last_name',
        'users__email')
    list_filter = ('school', 'type')

admin.site.register(models.Document, DocumentAdmin)


class QuestionnaireVariantDocumentGenerationConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'variant', 'document_type')
    list_filter = ('document_type', )

admin.site.register(models.QuestionnaireVariantDocumentGenerationCondition,
                    QuestionnaireVariantDocumentGenerationConditionAdmin)


admin.site.register(models.FillPaymentInfoEntranceStep,
                    modules.entrance.admin.AbstractEntranceStepAdmin)
