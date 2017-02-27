import abc
import json

from django.db.models import query_utils
from django.utils import safestring
import django.template


class ColumnDataType(abc.ABC):
    @abc.abstractmethod
    def render(self, obj, cell):
        """ Render one cell of table """


class StringDataType(ColumnDataType):
    def render(self, obj, cell):
        return str(cell)


class NumberDataType(ColumnDataType):
    def render(self, obj, cell):
        return str(int(cell))


class RawHtmlDataType(ColumnDataType):
    def render(self, obj, cell):
        return safestring.mark_safe(str(cell))


class LinkDataType(ColumnDataType):
    """
        Usage: LinkDataType(StringDataType(), lambda obj: reverse('view:name', obj.id))
    """
    def __init__(self, parent_data_type, link_function):
        self.parent_data_type = parent_data_type
        self.link_function = link_function
        self.link_template = (django.template.engines['django']
            .from_string('<a href="{{ link }}">{{ data }}</a>'))

    def render(self, obj, cell):
        data = self.parent_data_type.render(obj, cell)
        link = self.link_function(obj)
        return self.link_template.render(django.template.Context({
            'link': link,
            'data': data,
        }))


class Column(abc.ABC):
    """
    short_name: str, i.e. 'age'
    title: str, i.e. 'Возраст'
    order_filter: list or tuple, acceptable as args for Django queryset's .order_by(). I.e. ('age', 'class')
    order_function: if order_filter is None, order_function is applied to each row like a `key` param of `sorted`
    search_filter: function filter → dict, dict should be acceptable as kwargs for Django Q-object.
        I.e. search_filter = lambda s: Q(age__gte=s)
    search_function: if search_filter is None, search_function is applied to each row and should return True or False
        I.e. search_function = lambda obj, s: obj.age >= s

    Important: Usage of order_function or search_function can be expensive.
    """
    name = ''
    title = ''

    order_filter = None
    order_function = None

    search_filter = None
    search_function = None

    data_type = StringDataType()

    def __init__(self):
        pass

    @property
    def is_sortable(self):
        return self.order_filter is not None or self.order_function is not None

    @property
    def is_searchable(self):
        return self.search_filter is not None or self.search_function is not None

    @abc.abstractmethod
    def get_cell_data(self, table, obj):
        """ This method is called for extracting one cell for table """


class SimplePropertyColumn(Column):
    def __init__(self, attr_name, title, name=None, search_attrs=None):
        super().__init__()
        self.attr_name = attr_name
        if name is None:
            self.name = self.attr_name
        else:
            self.name = name
        self.title = title
        self.order_filter = (self.attr_name, )

        if search_attrs is None:
            search_attrs = [attr_name]
        self.search_filter = lambda f: self.build_q(search_attrs, f)

    @staticmethod
    def build_q(search_attrs, filter):
        result = query_utils.Q()
        for search_attr in search_attrs:
            kwargs = {search_attr + '__icontains': filter}
            result = result | query_utils.Q(**kwargs)
        return result

    def get_cell_data(self, table, obj):
        if hasattr(obj, self.attr_name):
            attr = getattr(obj, self.attr_name)
            if callable(attr):
                return attr()
            return attr
        return ''


class SimpleFuncColumn(Column):
    def __init__(self, func, title, name=None):
        super().__init__()
        self.func = func
        self.title = title
        if name is None:
            self.name = func.__name__
        else:
            self.name = name
        self.order_function = lambda obj: self.func(obj)
        self.search_function = lambda obj, f: f in self.func(obj)

    def get_cell_data(self, table, obj):
        return self.func(obj)


class IndexColumn(Column):
    name = 'index'

    def __init__(self, start_from=1):
        super().__init__()
        self.counter = start_from

    def get_cell_data(self, table, obj):
        current_number = self.counter
        self.counter += 1
        return current_number


class Table(abc.ABC):
    icon = None

    title = ''

    columns = tuple()

    identifiers = {}

    # Replace with special search widget
    search_enabled = True

    # Set to None for unlimited page
    page_size = 10

    def __init__(self, model, queryset):
        self.model = model
        self.queryset = queryset

    @abc.abstractmethod
    def get_header(self):
        """
        :return: Header of the table. Not used now
        """

    @classmethod
    @abc.abstractclassmethod
    def restore(cls, identifiers):
        """
        Recreate the table from identifiers. I.e. Table.restore(some_table.identifiers)
        :param identifiers: MultiValueDict
        """

    def apply_filter(self, filter):
        """ Applies filter to table's queryset """
        filter_words = filter.split()

        common_qs = self.model.objects.all()
        for filter_word in filter_words:
            filter_word_qs = self.model.objects.none()
            for column in self.columns:
                if column.is_searchable:
                    # TODO: move this logic to Column
                    if column.search_filter is not None:
                        search_filter = column.search_filter(filter_word)
                        column_qs = self.queryset.filter(search_filter)
                        filter_word_qs = filter_word_qs | column_qs
                    elif column.search_function is not None:
                        # TODO
                        pass
            common_qs = common_qs & filter_word_qs
        self.queryset = common_qs
        self.after_filter_applying()

    @abc.abstractmethod
    def after_filter_applying(self):
        """ Callback called after self.apply_filter(), used for extracting extra data for filtered rows if needed """

    @property
    def paged_queryset(self):
        if self.page_size is None:
            return self.queryset
        return self.queryset[:self.page_size]

    def rows(self):
        for obj in self.paged_queryset:
            row = []
            for column in self.columns:
                cell_data = column.get_cell_data(self, obj)
                cell = column.data_type.render(obj, cell_data)

                row.append(cell)

            yield row

    @property
    def table_name(self):
        return '%s.%s' % (self.__class__.__module__, self.__class__.__name__)

    @property
    def table_identifiers_json(self):
        return json.dumps(self.identifiers)
