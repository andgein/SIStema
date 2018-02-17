from django.db import models
import django.db.migrations.writer
from django.conf import settings

from cached_property import cached_property
import relativefilepathfield.fields
import polymorphic.models

import schools.models
import generator.models
import users.models
import questionnaire.models


__all__ = ['DocumentType',
           'Document',
           'AbstractDocumentGenerationCondition',
           'QuestionnaireVariantDocumentGenerationCondition'
           ]


class DocumentType(models.Model):
    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. '
                  'Лучше обойтись латинскими буквами, цифрами и подчёркиванием'
    )

    school = models.ForeignKey(
        schools.models.School,
        related_name='finance_document_types',
        on_delete=models.CASCADE,
    )

    session = models.ForeignKey(
        schools.models.Session,
        related_name='+',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
        help_text='Документ будет показан только школьникам, зачисленным в эту смену'
    )

    name = models.TextField()

    additional_information = models.TextField(
        help_text='Показывается школьнику перед скачиванием.'
                  'Например, «Распечатайте его в двух экземплярах, '
                  'подпишите со своей стороны и привезите в ЛКШ»',
        blank=True,
    )

    template = models.ForeignKey(
        generator.models.Document,
        related_name='+',
        on_delete=models.CASCADE,
    )

    required_questions = models.ManyToManyField(
        questionnaire.models.AbstractQuestionnaireQuestion,
        related_name='+',
        blank=True,
    )

    class Meta:
        unique_together = ('school', 'short_name')

    def __str__(self):
        return '%s. %s' % (self.school, self.name)

    def save(self, *args, **kwargs):
        if self.session is not None and self.session.school_id != self.school_id:
            raise ValueError('Session should belong to the same school ')
        super().save(*args, **kwargs)

    def is_need_for_user(self, user):
        # If session is defined check that user has been enrolled in it
        if self.session is not None:
            entrance_status = (
                user.entrance_statuses.filter(school=self.school).first()
            )
            if (entrance_status is not None and
               entrance_status.is_enrolled and
               entrance_status.session_id != self.session.id):
                return False

        # Document is need for user if there is no generation conditions for it
        # or if it is satisfied at least one of them
        conditions = self.generation_conditions.all()

        if len(conditions) == 0:
            return True

        for condition in conditions:
            if condition.is_satisfied(user):
                return True

        return False


class Document(models.Model):
    school = models.ForeignKey(schools.models.School, on_delete=models.CASCADE)

    users = models.ManyToManyField(users.models.User)

    type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name='generated_documents',
    )

    filename = relativefilepathfield.fields.RelativeFilePathField(
        path=django.db.migrations.writer.SettingsReference(
            settings.SISTEMA_FINANCE_DOCUMENTS,
            'SISTEMA_FINANCE_DOCUMENTS'
        ),
        recursive=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def _users_list(self):
        return ', '.join(str(u) for u in self.users.all())


class AbstractDocumentGenerationCondition(polymorphic.models.PolymorphicModel):
    document_type = models.ForeignKey(
        DocumentType,
        related_name='generation_conditions',
        on_delete=models.CASCADE,
    )

    def is_satisfied(self, user):
        raise NotImplementedError('Child should implement is_satisfied()')


class QuestionnaireVariantDocumentGenerationCondition(AbstractDocumentGenerationCondition):
    variant = models.ForeignKey(
        questionnaire.models.ChoiceQuestionnaireQuestionVariant,
        related_name='+',
        on_delete=models.CASCADE,
    )

    @cached_property
    def question(self):
        return self.variant.question

    def is_satisfied(self, user):
        qs = questionnaire.models.QuestionnaireAnswer.objects.filter(
            questionnaire_id=self.question.questionnaire_id,
            question_short_name=self.question.short_name,
            user=user,
            answer=self.variant.id
        )
        return qs.exists()
