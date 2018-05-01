import mimetypes
import os
import urllib.parse
import collections

from django.conf import settings
from django.http import HttpResponse
from django.http.response import HttpResponseNotFound
import django.db
import django.utils.text


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

    # We define 'filename*' parameter following RFC2231 (encoding extension in
    # HTTP headers). See http://greenbytes.de/tech/tc2231/ for more details.
    filename_param = (
        'filename*=UTF-8\'\'' + urllib.parse.quote(original_filename))
    response['Content-Disposition'] = 'attachment; ' + filename_param

    # Disable htmlmin minifying for this response because htmlmin works only with UTF-8 files
    # and can raise exception if file is not valid. Some files returned via this file are
    # user's uploaded files so we can't guarantee that they are safe.
    response.minify_response = False

    return response


# TODO: if extract_key_function is str, make extract_key_function from operator.attrgetter
def group_by(collection, extract_key_function, extract_value_function=None):
    """
    Group collection by the specified key.

    :param collection: The collection to group
    :param extract_key_function: `collection element -> key` function
    :param extract_value_function: `collection element -> value` function
    :return: {key: [value]} dict
    """
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
