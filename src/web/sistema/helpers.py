import enum
import mimetypes
import operator
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


# noinspection PyPep8Naming
class GroupByAggregator:
    def __init__(self, function, result_type=None):
        self.function = function
        self.result_type = result_type

    def aggregate(self, collection):
        return self.function(collection)

    # We create these aggregators as static methods (not as fields) because
    # fields can't use constructor calls
    @staticmethod
    def COUNT():
        return GroupByAggregator(len, int),

    @staticmethod
    def SORTED():
        return GroupByAggregator(sorted, list),

    @staticmethod
    def FIRST_ELEMENT():
        return GroupByAggregator(operator.itemgetter(0))

    @staticmethod
    def LAST_ELEMENT():
        return GroupByAggregator(operator.itemgetter(-1))


# TODO: if extract_key_function is str, make extract_key_function from operator.attrgetter
def group_by(collection, extract_key_function, extract_value_function=None,
             aggregator=None):
    """
    Group collection by the specified key.

    :param collection: The collection to group
    :param extract_key_function: `collection element -> key` function
    :param extract_value_function: `collection element -> value` function
    :param aggregator: GroupByAggregator object. I.e. pass
        GroupByAggregate.COUNT() to return len of group instead of each group
    :return: {key: [value]} dict
    """
    if extract_value_function is None:
        def extract_value_function(x):
            return x

    grouped = collections.defaultdict(list)
    for item in collection:
        key = extract_key_function(item)
        value = extract_value_function(item)
        grouped[key].append(value)

    if aggregator is not None:
        if aggregator.result_type is not None:
            result = collections.defaultdict(aggregator.result_type)
        else:
            # Try to guess process_group_function's output type by calling it
            # on first group
            if len(grouped) > 0:
                first_group = list(grouped.values())[0]
                result = collections.defaultdict(type(aggregator.aggregate(first_group)))
            else:
                result = collections.defaultdict(list)
        for key in grouped.keys():
            result[key] = aggregator.aggregate(grouped[key])
        return result

    return grouped


def nested_group_by(collection, *extract_key_functions, extract_value_function=None,
                    aggregator=None):
    """
    Group collection by specified attributes

    :param collection: The collection to group
    :param extract_key_functions: List of key functions
    :param extract_value_function: `collection element -> value` function
    :param aggregator: GroupByAggregator object. I.e. pass
        GroupByAggregate.COUNT() to return len of group instead of each group
    :return: dict of dict ... of dicts of values
        { first_attribute_value: { second_attribute_value: [items...] ... } ... }
    """
    if len(extract_key_functions) == 0:
        if aggregator is not None:
            return aggregator.aggregate(collection)
        return collection

    is_last_step = len(extract_key_functions) == 1

    def recursive_process_group_function(c):
        return nested_group_by(
            c,
            *extract_key_functions[1:],
            extract_value_function=extract_value_function,
            aggregator=aggregator
        )

    return group_by(
        collection,
        extract_key_functions[0],
        # Extract values only on last step
        extract_value_function=extract_value_function if is_last_step else None,
        aggregator=GroupByAggregator(recursive_process_group_function)
    )


def list_to_dict(collection, *functions):
    """
    Converts list into dict. Example:
        ```
        > data = [{'first_name': 'Andrew', 'last_name': 'Gein'}, {'first_name': 'Peter', 'last_name': 'The Great'}]
        > list_to_dict(data, operator.itemgetter('first_name'), operator.itemgetter('last_name'))
        {'Andrew': 'Gein', 'Peter': 'The Great'}
        ```
    Supports nested dicts and several key extract functions.
    :param collection: list of any objects
    :param functions: list of functions. All functions except the last one are
        key extract functions, last function is value extract function.
    :return: dict
    """
    if len(functions) < 2:
        raise ValueError('list_to_dict: count of functions should be at least 2')
    return nested_group_by(
        collection,
        *functions[:-1],
        extract_value_function=functions[-1],
        aggregator=GroupByAggregator.FIRST_ELEMENT()
    )


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
