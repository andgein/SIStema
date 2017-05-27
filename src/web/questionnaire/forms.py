from django import forms


class QuestionnaireForm(forms.Form):
    def __init__(self, initial=None, *args, **kwargs):
        super().__init__(*args, initial=initial, **kwargs)

        for field_id, field in self.fields.items():
            if hasattr(field, 'update_with_initial'):
                field.update_with_initial(self.initial.get(field_id))


class ChoiceQuestionField(forms.Field):
    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question

    def update_with_initial(self, initial):
        # Disable question if user has checked variant which is marked as `disable_question_if_chosen`
        if initial:
            if self.question.is_multiple:
                qs = self.question.variants.filter(id__in=initial, disable_question_if_chosen=True)
            else:
                qs = self.question.variants.filter(id=initial, disable_question_if_chosen=True)
            if qs.exists():
                self.disabled = True


class TypedMultipleChoiceFieldForChoiceQuestion(ChoiceQuestionField, forms.TypedMultipleChoiceField):
    pass


class TypedChoiceFieldForChoiceQuestion(ChoiceQuestionField, forms.TypedChoiceField):
    pass


class QuestionnaireTypingDynamicsForm(forms.Form):
    prefix = 'typing-dynamics'

    # TODO(artemtab): look into compressing data before sending
    # We send about 100 characters for each keypress
    typing_data = forms.CharField(max_length=10000 * 100,
                                  widget=forms.HiddenInput())
