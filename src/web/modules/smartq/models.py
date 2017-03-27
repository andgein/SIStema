import collections
import datetime
import json
import multiprocessing.pool
import random
import time
import traceback
import types

from django import forms
from django.db import models
import django.core.mail
import django.urls

from cached_property import cached_property
from constance import config
import jinja2

from modules.smartq import api
import frontend.forms
import users.models

# TODO(Artem Tabolin): consider replacing with
#     https://pypi.python.org/pypi/pysandbox/
class Sandbox:
    """
    A simple sandbox to execute code stored in a database. Allows to run
    functions in a separate thread with a timeout. Passes all the exceptions
    over adding TimeoutException to them.
    """
    @classmethod
    def instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.pool = multiprocessing.pool.ThreadPool(processes=1)

    def run(self, function, args=None, kwargs=None, timeout=None):
        args = args or []
        kwargs = kwargs or {}

        async_result = self.pool.apply_async(function, args, kwargs)
        return async_result.get(timeout)


class Question(models.Model):
    short_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Используется в url'ах. Например, build-heap.")

    template_html = models.TextField(
        help_text='Jinja2 шаблон для HTML кода вопроса.')

    template_css = models.TextField(
        blank=True,
        default='',
        help_text='Jinja2 шаблон для CSS кода вопроса.')

    template_js = models.TextField(
        blank=True,
        default='',
        help_text='Jinja2 шаблон для Javascript кода вопроса.')

    # TODO(Artem Tabolin): consider adding version control
    # TODO(Artem Tabolin): add a link to documentation to the help text. As soon
    #     as we have it.
    code = models.TextField(
        help_text='Код python модуля, в котором должны быть определены классы '
                  'Generator и Checker. В модуле изначально доступен модуль '
                  'api. Generator и Checker должны быть отнаследованы от '
                  'api.Generator и api.Checker соответственно.')

    # TODO(Artem Tabolin): cache compiled code in a database

    created_date = models.DateTimeField(auto_now_add=True)

    modified_date = models.DateTimeField(auto_now=True)

    _implementation_cache = {}
    _template_cache = {}

    def __str__(self):
        return self.short_name

    @property
    def _module_name(self):
        return self.short_name.replace('-', '_')

    @property
    def _implementation(self):
        name = self._module_name
        module = self._implementation_cache.get(name)
        if module is None or module.modified_date < self.modified_date:
            try:
                module = types.ModuleType(name=name)
                module.api = api

                Sandbox.instance().run(
                    exec,
                    [self.code, module.__dict__],
                    timeout=config.SMARTQ_MODULE_EXECUTION_TIMEOUT)
                module.modified_date = self.modified_date

                self._implementation_cache[name] = module
            except Exception:
                message = ('{}: smartq: failed running quesiton code\n'
                           '  question = {}\n'
                           '{}\n'.format(datetime.datetime.now(),
                                         self,
                                         traceback.format_exc()))
                print(message)
                django.core.mail.mail_admins(
                    'smartq: failed running question code', message)

                # TODO(Artem Tabolin): fail in a more graceful way. It should be
                #     easy for the code using smartq to show some kind of
                #     "Something went wrong" screen to the user.
                raise

        return module

    def _compiled_template(self, kind, template):
        key = '{}:{}'.format(kind, self.short_name)
        if key not in self._template_cache:
            self._template_cache[key] = jinja2.Template(template)

        return self._template_cache[key]

    @property
    def compiled_template_html(self):
        return self._compiled_template('html', self.template_html)

    @property
    def compiled_template_css(self):
        return self._compiled_template('css', self.template_html)

    @property
    def compiled_template_js(self):
        return self._compiled_template('js', self.template_html)

    def save(self, *args, **kwargs):
        # Check that the code actually compiles. It will throw an exception and
        # prevent saving if not.
        compile(self.code, self._module_name, 'exec')

        super().save(*args, **kwargs)

    def create_instance(self, user, seed=None, klass=None):
        if seed is None:
            seed = time.time()

        if klass is None:
            klass = GeneratedQuestion

        if not issubclass(klass, GeneratedQuestion):
            raise ValueError("Generated question class should be a subclass "
                             "of GeneratedQuestion")

        # Make it possible to store seed in a database
        seed = str(seed)[:100]

        # Standard python random is used because we don't need results to be
        # consistent across different python version and hardware. All the
        # generated data is stored in the database along with the original seed,
        # so we don't need to regenerate it.
        try:
            state = random.getstate()
            random.seed(seed)

            generator = Sandbox.instance().run(
                self._implementation.Generator,
                timeout=config.SMARTQ_GENERATOR_INSTANTIATION_TIMEOUT,
            )
            data = Sandbox.instance().run(
                generator.generate,
                timeout=config.SMARTQ_GENERATOR_TIMEOUT,
            )
        except Exception:
            message = ('{}: smartq: failed while generating quesiton\n'
                       '  question = {}\n'
                       '  user = {}\n'
                       '  seed = {}\n'
                       '{}\n'.format(datetime.datetime.now(),
                                     self,
                                     user,
                                     seed,
                                     traceback.format_exc()))

            print(message)
            django.core.mail.mail_admins(
                'smartq: failed while generating question', message)

            # TODO(Artem Tabolin): fail in a more graceful way. It should be
            #     easy for the code using smartq to show some kind of
            #     "Something went wrong" screen to the user.
            raise
        finally:
            random.setstate(state)

        return klass.objects.create(
            base_question=self,
            user=user,
            seed=seed,
            data_json=json.dumps(data.__dict__))


class GeneratedQuestion(models.Model):
    base_question = models.ForeignKey(Question)

    seed = models.CharField(
        max_length=100,
        help_text='По-умолчанию устанавливается в текущее системное время. '
                  'Используется только для отладки, так как сгенерированные '
                  'для вопроса данные целиком храняться в базе.',
    )

    user = models.ForeignKey(
        users.models.User,
        related_name='+',
        help_text='Пользователь, которому выдан этот вопрос. Другие '
                  'пользователи не смогут на него отвечать.',
    )

    data_json = models.TextField(
        help_text='Возвращённый генератором объект, сериализованный в JSON'
    )

    answer_json = models.TextField(
        blank=True,
        help_text='Последний ответ на вопрос, сериализованный в JSON'
    )

    # TODO(Artem Tabolin): consider using custom ModelManager which does
    #     serialization inside?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data_dict = json.loads(self.data_json)
        self.data = api.GeneratedQuestionData(**data_dict)
        self._form = None

    def __str__(self):
        return '{}({})'.format(self.base_question, self.seed)

    @cached_property
    def form_type(self):
        if self.id is None:
            return None

        return _make_form_type(
            self.id, self._question_div_id, self.data.answer_fields)

    @property
    def form(self):
        if self._form is None:
            self._form = self.form_type(self.answer)
        return self._form

    @form.setter
    def form(self, value):
        self._form = value

    @property
    def answer(self):
        return json.loads(self.answer_json) if self.answer_json else None

    @answer.setter
    def answer(self, value):
        self.answer_json = json.dumps(value)

    def save_answer(self, data):
        self.answer = {
            field.html_name: data[field.html_name]
            for field in self.form
            if field.html_name in data
        }
        self.form = self.form_type(self.answer)
        self.save()

    def html(self):
        rendered_template = (jinja2.Template(self.base_question.template_html)
                             .render(self._template_context))
        return '<div id="{}" class="smartq-question">{}</div>'.format(
            self._question_div_id, rendered_template)

    def css(self):
        return (jinja2.Template(self.base_question.template_css)
                .render(self._template_context))

    def js(self):
        rendered_template = (jinja2.Template(self.base_question.template_js)
                             .render(self._template_context))
        return '(function() {{ {} }})();'.format(rendered_template)

    @property
    def _template_context(self):
        return {
            'short_name': self.base_question.short_name,
            'question_id': self.id,
            'question_html_id': self._question_div_id,
            'data': self.data,
            'form': self.form,
        }

    @property
    def _question_div_id(self):
        return 'smartq-' + str(self.id)

    def check_answer(self, data):
        self.save_answer(data)

        if not self.form.is_valid():
            return api.CheckerResult(
                status=api.Checker.Status.PRESENTATION_ERROR)

        answer_dict = collections.OrderedDict(
            (name, self.form.cleaned_data[name])
            for name in self.form.field_order)

        result = None
        try:
            checker = Sandbox.instance().run(
                self.base_question._implementation.Checker,
                timeout=config.SMARTQ_CHECKER_INSTANTIATION_TIMEOUT
            )
            result = Sandbox.instance().run(
                checker.check,
                args=[self.data, answer_dict],
                timeout=config.SMARTQ_CHECKER_TIMEOUT
            )
        except Exception:  #pylint: disable=broad-except
            result = api.CheckerResult(
                status=api.Checker.Status.CHECK_FAILED,
                message="{}: [id={}, question={}] {}".format(
                    datetime.datetime.now(),
                    self.id,
                    self,
                    traceback.format_exc()
                )
            )

        if result.status == api.Checker.Status.CHECK_FAILED:
            message = ('{}: smartq: CheckFailed\n'
                       '  generated_question_id = {}\n'
                       '  question = {}\n'
                       '{}\n'.format(datetime.datetime.now(),
                                     self.id,
                                     self,
                                     result.message))
            print(message)
            django.core.mail.mail_admins('smartq: CheckFailed', message)

        return result


# TODO(Artem Tabolin): move to a separate module with staff models
class StaffGeneratedQuestion(GeneratedQuestion):
    @classmethod
    def get_instance(cls, user, base_question):
        try:
            instance = cls.objects.get(
                user=user,
                base_question=base_question)
        except cls.DoesNotExist:
            instance = base_question.create_instance(user, klass=cls)

        return instance

    @classmethod
    def regenerate(cls, user, base_question):
        cls.objects.filter(
            user=user,
            base_question=base_question
        ).delete()

        return base_question.create_instance(user, klass=cls)


def _make_form_type(generated_question_id, prefix, field_specs):
    fields = {}
    field_order = []

    for i, spec in enumerate(field_specs):
        field_name = spec.get('name', 'element_' + str(i))

        # Attributes to add to the input tag
        attrs = {
            'data-smartq-id': generated_question_id,
            'data-smartq-save-url': django.urls.reverse(
                'smartq:save_answer',
                kwargs={'generated_question_id': generated_question_id}
            ),

        }
        if 'validation_regexp' in spec:
            attrs['data-smartq-validation-regexp'] = spec['validation_regexp']
        if 'validation_regexp_message' in spec:
            attrs['data-smartq-validation-regexp-message'] = (
                spec['validation_regexp_message'])
        if 'placeholder' in spec:
            attrs['placeholder'] = spec['placeholder']

        required = spec.get('required', True)

        field = None
        if spec['type'] == api.AnswerFieldSpec.Type.TEXT:
            if spec['multiline']:
                widget = frontend.forms.SistemaTextarea(attrs=attrs)
            else:
                widget = frontend.forms.SistemaTextInput(attrs=attrs)

            field = forms.CharField(
                required=required,
                min_length=spec.get('min_length'),
                max_length=spec.get('max_length'),
                widget=widget)

        if spec['type'] == api.AnswerFieldSpec.Type.INTEGER:
            field = forms.IntegerField(
                required=required,
                min_value=spec.get('min_value'),
                max_value=spec.get('max_value'),
                widget=frontend.forms.SistemaNumberInput(attrs=attrs))

        if field is None:
            raise ValueError('Unknown field type')

        fields[field_name] = field
        field_order.append(field_name)

    return type('SmartQForm', (forms.BaseForm,), {
        'default_renderer': 'django.forms.renderers.Jinja2',
        'base_fields': fields,
        'field_order': field_order,
        'prefix': prefix,
    })
