import re
import wiki.plugins.attachments.markdown_extensions
import django.core.exceptions
from django.utils.deprecation import MiddlewareMixin


# TODO(artemtab): remove once the bug is fixed
# Workaround for bug in wiki:
# https://github.com/django-wiki/django-wiki/issues/885
class WikiWorkaroundMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        # Replace regex for finding attachment tags with the custom one to
        # prevent `array[size]` from being detecated as an attachment tag
        wiki.plugins.attachments.markdown_extensions.ATTACHMENT_RE = re.compile(
            r'(?P<before>.*)\[ *(attachment\:(?P<id>[0-9]+))( *((title\:\"(?P<title>[^\"]+)\")|(?P<size>size)))*\](?P<after>.*)',
            re.IGNORECASE)
        raise django.core.exceptions.MiddlewareNotUsed()
