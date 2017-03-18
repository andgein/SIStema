import enum

class Generator:
    def generate(self):
        raise NotImplementedError()


class Checker:
    class Result(enum.IntEnum):
        # Use explicit values and don't change the existing ones. That's
        # important because they are stored in the database.
        OK = 1
        WrongAnswer = 2
        PresentationError = 3
        CheckFailed = 4

    def check(self, generated_question_data, answer):
        raise NotImplementedError()


class GeneratedQuestionData:
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

        if getattr(self, 'answer_fields', None) is None:
            self.answer_fields = [AnswerFieldSpec.text()]


class CheckerResult:
    def __init__(self, status, message=None, field_messages=None):
        self.status = status
        self.message = message or ''
        self.field_messages = field_messages or {}

        if not isinstance(self.status, Checker.Result):
            raise TypeError('status should be of api.Checker.Result')

        if not isinstance(self.message, str):
            raise TypeError('message should be an instance of str')

        if not isinstance(self.field_messages, dict):
            raise TypeError('field_message should be a dict from field names '
                            'to messages')

class AnswerFieldSpec:
    class Type(enum.IntEnum):
        # Use explicit values and don't change the existing ones. That's
        # important because they are stored in the database.
        TEXT = 1
        INTEGER = 2

    @classmethod
    def _base(cls, name=None):
        spec = {'type': cls.Type.TEXT}

        if name is not None:
            spec['name'] = name

        return spec

    @classmethod
    def text(cls,
             min_length=None,
             max_length=None,
             multiline=False,
             validation_regexp=None,
             **kwargs):
        spec = cls._base(**kwargs)

        if not isinstance(multiline, bool):
            raise ValueError('multiline must be either True or False')

        spec['multiline'] = multiline

        # TODO(Artem Tabolin): can we avoid code duplication?
        if min_length is not None:
            if not isinstance(min_length, int) or min_length < 0:
                raise TypeError('min_length must be a non-negative integer')
            spec['min_length'] = min_length

        if max_length is not None:
            if not isinstance(max_length, int) or max_length < 0:
                raise TypeError('max_length must be a non-negative integer')
            spec['max_length'] = max_length

        if validation_regexp is not None:
            if not isinstance(validation_regexp, str):
                raise TypeError('validation_regexp must be a string')
            spec['validation_regexp'] = validation_regexp

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
