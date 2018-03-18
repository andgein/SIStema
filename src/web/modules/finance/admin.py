from django.contrib import admin

import modules.entrance.admin
import modules.entrance.models
import questionnaire.models
import users.models
from modules.finance import models


@admin.register(models.PaymentAmount)
class PaymentAmountAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'amount')
    list_filter = ('school',)
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username')
    autocomplete_fields = ('user',)


@admin.register(models.Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'user', 'type', 'amount', 'private_comment',
                    'public_comment')
    list_filter = ('school', 'type')
    autocomplete_fields = ('user',)
    search_fields = (
        'user__profile__first_name',
        'user__profile__last_name',
        'user__username',
        'private_comment',
        'public_comment')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = (
                users.models.User.objects
                .filter(entrance_statuses__status=
                        modules.entrance.models.EntranceStatus.Status.ENROLLED)
                .distinct()
                .order_by('profile__last_name', 'profile__first_name')
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(
    models.PaymentInfoQuestionnaireBlock,
    questionnaire.admin.AbstractQuestionnaireBlockChildAdmin,
)


@admin.register(models.DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'short_name', 'name')
    list_display_links = ('id', 'short_name')
    autocomplete_fields = ('session', 'template', 'required_questions')
    search_fields = ('short_name', 'name')
    list_filter = ('school', )


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'type', '_users_list', 'created_at')
    autocomplete_fields = ('users', 'type')
    search_fields = (
        'users__profile__first_name',
        'users__profile__last_name',
        'users__email')
    list_filter = ('school', 'type')


@admin.register(models.QuestionnaireVariantDocumentGenerationCondition)
class QuestionnaireVariantDocumentGenerationConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'variant', 'document_type')
    list_filter = ('document_type', )
    autocomplete_fields = ('document_type', 'variant')


@admin.register(models.FillPaymentInfoEntranceStep)
class FillPaymentInfoEntranceStepAdmin(
        modules.entrance.admin.EntranceStepChildAdmin):
    autocomplete_fields = (
        modules.entrance.admin.EntranceStepChildAdmin.autocomplete_fields +
        ('questionnaire',))


@admin.register(models.DocumentsEntranceStep)
class DocumentsEntranceStepAdmin(modules.entrance.admin.EntranceStepChildAdmin):
    autocomplete_fields = (
        modules.entrance.admin.EntranceStepChildAdmin.autocomplete_fields +
        ('document_types',))
