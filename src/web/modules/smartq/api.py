import enum


class Generator:
    def generate(self):
        """
        The method should return a GeneratedQuestionData object. It will be
        passed to Checker and to the html, css and js templates. You may pass
        any keyword arguments to the constructor. They will be available as
        attributes.

        See GeneratedQuestionData's documentation for any special arguments it
        has.
        """
        raise NotImplementedError()


class Checker:
    # Modify together with topics
    class Status(enum.IntEnum):
        # Use explicit values and don't change the existing ones. That's
        # important because they are stored in the database.
        OK = 1
        WRONG_ANSWER = 2
        PRESENTATION_ERROR = 3
        CHECK_FAILED = 4

    def check(self, generated_question_data, answer):
        """
        The method should return a CheckerResult object.

        :generated_question_data: GeneratedQuestionData object returned by
            generator
        :answer: Ordered dict with "field name" -> "user input" mapping
        ::
        """
        raise NotImplementedError()


class GeneratedQuestionData:
    def __init__(self, **kwargs):
        """
        All the keyword arguments will be set as attributes.

        :answer_fields: List of specs for answer fields as returned by
            AnswerFieldSpec class methods. Default is a single text field.
        """
        for name, value in kwargs.items():
            setattr(self, name, value)

        if getattr(self, 'answer_fields', None) is None:
            self.answer_fields = [AnswerFieldSpec.text()]


class CheckerResult:
    def __init__(self, status, message=None, field_messages=None):
        """
        :status: value of Checker.Status enum
        :self.message: message not specific to any field
        :self.field: dict from field names to field specific messages
        """
        self.status = status
        self.message = message or ''
        self.field_messages = field_messages or {}

        if not isinstance(self.status, Checker.Status):
            raise TypeError('status should be of api.Checker.Status')

        if not isinstance(self.message, str):
            raise TypeError('message should be an instance of str')

        if not isinstance(self.field_messages, dict):
            raise TypeError('field_message should be a dict from field names '
                            'to messages')

    @property
    def is_ok(self):
        return self.status == Checker.Status.OK


class AnswerFieldSpec:
    class Type(enum.IntEnum):
        # Use explicit values and don't change the existing ones. That's
        # important because they are stored in the database.
        TEXT = 1
        INTEGER = 2

    @classmethod
    def _base(cls, name=None, required=True, placeholder=None):
        spec = {'type': cls.Type.TEXT}

        if name is not None:
            spec['name'] = name

        if not isinstance(required, bool):
            return TypeError('required must be either True or False')
        spec['required'] = required

        if placeholder is not None:
            spec['placeholder'] = str(placeholder)

        return spec

    @classmethod
    def text(cls,
             min_length=None,
             max_length=None,
             multiline=False,
             validation_regexp=None,
             validation_regexp_message=None,
             **kwargs):
        spec = cls._base(**kwargs)

        if not isinstance(multiline, bool):
            raise TypeError('multiline must be either True or False')

        spec['multiline'] = multiline

        # TODO(Artem Tabolin): can we avoid code duplication?
        if min_length is not None:
            if not isinstance(min_length, int):
                raise TypeError('min_length must be an integer')
            if min_length < 0:
                raise ValueError('min_length must be non-negative')
            spec['min_length'] = min_length

        if max_length is not None:
            if not isinstance(max_length, int):
                raise TypeError('max_length must be an integer')
            if max_length < 0:
                raise ValueError('max_length must be non-negative')
            spec['max_length'] = max_length

        if validation_regexp is not None:
            if not isinstance(validation_regexp, str):
                raise TypeError('validation_regexp must be a string')
            spec['validation_regexp'] = validation_regexp

        if validation_regexp_message is not None:
            if not isinstance(validation_regexp_message, str):
                raise TypeError('validation_regexp_message must be a string')
            spec['validation_regexp_message'] = validation_regexp_message

        return spec

    @classmethod
    def integer(cls, min_value=None, max_value=None, **kwargs):
        spec = cls.text(**kwargs)
        spec['type'] = cls.Type.INTEGER

        if min_value is not None:
            if not isinstance(min_value, int):
                raise TypeError('min_value must be an integer')
            spec['min_value'] = min_value

        if max_value is not None:
            if not isinstance(max_value, int):
                raise TypeError('max_value must be an integer')
            spec['max_value'] = max_value

        return spec
