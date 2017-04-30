import mimetypes
import os
import urllib.parse
import collections

from django.http import HttpResponse
from django.http.response import HttpResponseNotFound
from django.conf import settings
import django.db


def respond_as_attachment(request, file_path, original_filename):
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return HttpResponseNotFound()

    with open(file_path, 'rb') as fp:
        response = HttpResponse(fp.read())

    content_type, encoding = mimetypes.guess_type(original_filename)
    if content_type is None:
        content_type = 'application/octet-stream'
    response['Content-Type'] = content_type
    response['Content-Length'] = str(os.stat(file_path).st_size)
    if encoding is not None:
        response['Content-Encoding'] = encoding

    # To inspect details for the below code, see http://greenbytes.de/tech/tc2231/
    if u'MSIE' in request.META['HTTP_USER_AGENT']:
        # IE does not support internationalized filename at all.
        # It can only recognize internationalized URL, so we do the trick via routing rules.
        filename_header = ''
    else:
        # For others we follow RFC2231 (encoding extension in HTTP headers).
        filename_header = 'filename*=UTF-8\'\'%s' % urllib.parse.quote(original_filename)
    response['Content-Disposition'] = 'attachment; ' + filename_header
    return response


# TODO: if extract_key_function is str, make extract_key_function from operator.attrgetter
def group_by(collection, extract_key_function, extract_value_function=None):
    if extract_value_function is None:
        def extract_value_function(x):
            return x

    result = collections.defaultdict(list)
    for item in collection:
        key = extract_key_function(item)
        value = extract_value_function(item)
        result[key].append(value)

    return result


# MySQL optimization is bad for nested queries such as
# SELECT ... FROM ... WHERE id IN (SELECT id FROM ... WHERE ...)
# So this function evaluate the queryset and convert it to the list
def nested_query_list(queryset, use_db=None):
    if use_db is None:
        use_db = django.db.DEFAULT_DB_ALIAS
    is_mysql = 'mysql' in settings.DATABASES[use_db]['ENGINE'].lower()
    if is_mysql:
        return list(queryset)
    return queryset
