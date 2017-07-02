from django.contrib import admin
from django.db import models
import django.forms

from dal import autocomplete


def register_autocomplete_field_for_foreign_key(
        model_cls,
        url,
        queryset=None,
        placeholder='Поиск...',
        empty_label='----------------------------------------'):
    if queryset is None:
        queryset = model_cls.objects.all()

    def form_field_factory():
        return django.forms.ModelChoiceField(
            queryset=queryset,
            empty_label=empty_label,
            widget=autocomplete.ModelSelect2(
                url=url,
                attrs={'data-placeholder': placeholder, 'data-html': 'true'}
            )
        )

    register_form_field_for_foreign_key(model_cls, form_field_factory)


def register_form_field_for_foreign_key(model_cls, form_field_factory):
    SistemaAdminMixin.register_form_field_for_foreign_key(model_cls,
                                                          form_field_factory)


class AlreadyRegisteredException(Exception):
    pass


class SistemaAdminMixin:
    form_fields_for_foreign_keys = {}

    @classmethod
    def register_form_field_for_foreign_key(cls, model_cls, form_field_factory):
        if not issubclass(model_cls, models.Model):
            raise ValueError('Cannot register form field for class not derived '
                             'from django.db.modes.Model')
        if model_cls in cls.form_fields_for_foreign_keys:
            raise AlreadyRegisteredException(
                'Admin form field for {} is already registered'
                .format(model_cls.__name__))
        if not callable(form_field_factory):
            raise ValueError('Form field factory should be callable')

        cls.form_fields_for_foreign_keys[model_cls] = form_field_factory

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        form_field_factory = self.form_fields_for_foreign_keys.get(
            db_field.related_model)
        if form_field_factory is not None:
            return form_field_factory()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ModelAdmin(SistemaAdminMixin, admin.ModelAdmin):
    pass
