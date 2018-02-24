import six
from django import template
import sys
from django.conf import settings

register = template.Library()


# See django.template.defaulttags.URLNode for details
class UrlWithParamsNode(template.Node):
    def __init__(self, view_name, kwargs, asvar):
        self.view_name = view_name
        self.kwargs = template.Variable(kwargs)
        self.asvar = asvar

    def render(self, context):
        from django.urls import reverse, NoReverseMatch
        kwargs = self.kwargs.resolve(context)

        view_name = self.view_name.resolve(context)

        try:
            current_app = context.request.current_app
        except AttributeError:
            # Change the fallback value to None when the deprecation path for
            # Context.current_app completes in Django 1.10.
            current_app = context.current_app

        # Try to look up the URL twice: once given the view name, and again
        # relative to what we guess is the "main" app. If they both fail,
        # re-raise the NoReverseMatch unless we're using the
        # {% url ... as var %} construct in which case return nothing.
        url = ''
        try:
            url = reverse(view_name, kwargs=kwargs, current_app=current_app)
        except NoReverseMatch:
            exc_info = sys.exc_info()
            if settings.SETTINGS_MODULE:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                try:
                    url = reverse(project_name + '.' + view_name,
                                  kwargs=kwargs,
                                  current_app=current_app)
                except NoReverseMatch:
                    if self.asvar is None:
                        # Re-raise the original exception, not the one with
                        # the path relative to the project. This makes a
                        # better error message.
                        six.reraise(*exc_info)
            else:
                if self.asvar is None:
                    raise

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url


@register.tag
def url_with_params(parser, token):
    # See django.template.defaulttags.url for details
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError("'%s' takes at least one argument"
                                           " (path to a view)" % bits[0])
    viewname = parser.compile_filter(bits[1])
    kwargs = ''
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        if len(bits) != 1:
            raise template.TemplateSyntaxError('Expected one argument (dict) for url_with_params')
        kwargs = bits[0]

    return UrlWithParamsNode(viewname, kwargs, asvar)
