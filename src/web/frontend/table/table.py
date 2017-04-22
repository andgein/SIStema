from functools import reduce
from operator import and_
from operator import or_
import collections
import copy
import enum
import itertools

from django.db.models import Q
from django.utils.functional import cached_property
import django.db.models.query
import django.template

import django_tables2 as tables

from . import columns
from .utils import A


__all__ = ('Table',)


class BaseTable:
    class ExportFormat(enum.Enum):
        CSV = 'csv'

    def __init__(self,
                 qs,
                 data_url,
                 icon=None,
                 title=None,
                 pagination=None,
                 default_slice_length=None,
                 *args, **kwargs):
        if not isinstance(qs, django.db.models.query.QuerySet):
            raise TypeError('qs must be a QuerySet')

        self.columns = copy.deepcopy(type(self).base_columns)

        self.qs = qs
        self.initial_qs = qs
        self.filtered_qs = qs
        self.index = itertools.count(1)

        self.data_url = data_url
        self._dt2_table = None
        self._meta = getattr(self, '_meta', TableOptions())
        self._prefix = kwargs.get('prefix')
        self._icon = icon
        self._title = title
        self._pagination = pagination
        self._default_slice_length = default_slice_length

        if 'prefix' in kwargs:
            kwargs['prefix'] += '_'

    def slice(self, start=None, length=None):
        if start is None:
            start = 0
        if length is None:
            length = self.default_slice_length

        if length <= 0:
            return

        self.qs = self.qs[start:start + length]

    def order_by(self, *column_names):
        order_by_fields = []
        for column_name in column_names:
            direction = ''
            if column_name.startswith('-'):
                column_name = column_name[1:]
                direction = '-'

            column = self.columns.get(column_name)
            if column is not None and column.orderable:
                accessor_strs = column.order_by or (column.accessor,)

                order_by_fields.extend(
                    direction + '__'.join(A(accessor_str).bits)
                    for accessor_str in accessor_strs)

        self.qs = self.qs.order_by(*order_by_fields)

    def search_by(self, query, column_name=None):
        if column_name is None:
            # Global search
            search_method = getattr(self, 'search', None)
            if callable(search_method):
                self.qs = search_method(self.qs, query)
            else:
                tokens = query.split()
                search_lookups = [
                    A(accessor_str).django_lookup + '__icontains'
                    for column in self.columns.values()
                    if column.searchable
                    for accessor_str in (column.search_in or
                                         (column.accessor,))]
                global_search_lookup = reduce(and_, [
                    reduce(or_, [Q((lookup, token))
                                 for lookup in search_lookups])
                    for token in tokens])
                self.qs = self.qs.filter(global_search_lookup)
        else:
            # Column search
            search_method = getattr(self, 'search_' + column_name, None)
            if callable(search_method):
                self.qs = search_method(self.qs, query)
            else:
                # TODO: implement the default case
                pass

        self.filtered_qs = self.qs

    def filter_by(self, column_name, values):
        # TODO: filter
        self.filtered_qs = self.qs

    def as_plain_rows(self):
        # TODO: refactor not to rely much on django_tables2
        rows = []
        for row in self.dt2_table.rows:
            rows.append({column.name: cell for column, cell in row.items()})
        return rows

    @cached_property
    def dt2_table(self):
        return type(self).dt2_table_type(self.qs)

    @cached_property
    def prefix(self):
        return self._prefix if self._prefix is not None else self._meta.prefix

    def with_prefix(self, s):
        return s if not self.prefix else self.prefix + '_' + s

    def filter_column_arg(self, column_name):
        return self.with_prefix(self._meta.filter_arg + '_' + column_name)

    def search_column_arg(self, column_name):
        return self.with_prefix(self._meta.search_arg + '_' + column_name)

    @cached_property
    def search_arg(self):
        return self.with_prefix(self._meta.search_arg)

    @cached_property
    def order_by_arg(self):
        return self.with_prefix(self._meta.order_by_arg)

    @cached_property
    def slice_start_arg(self):
        return self.with_prefix(self._meta.slice_start_arg)

    @cached_property
    def slice_length_arg(self):
        return self.with_prefix(self._meta.slice_length_arg)

    @cached_property
    def icon(self):
        return self._icon if self._icon is not None else self._meta.icon

    @cached_property
    def title(self):
        return self._title if self._title is not None else self._meta.title

    @cached_property
    def pagination(self):
        return (self._pagination if self._pagination is not None
                else self._meta.pagination)

    @cached_property
    def pagination_options(self):
        if self.pagination is False:
            return ()
        if self.pagination is True:
            return (15, 20, 30, 50, 100)
        return self.pagination

    @cached_property
    def pagination_options_string(self):
        return ','.join(map(str, self.pagination_options))

    @cached_property
    def default_slice_length(self):
        if self._default_slice_length is not None:
            return self._default_slice_length
        else:
            return self._meta.default_slice_length

    @cached_property
    def search_enabled(self):
        # TODO: make it customizable
        return True


class TableOptions:
    def __init__(self, options=None):
        self.icon = getattr(options, 'icon', None)
        self.title = getattr(options, 'title', '')

        self.prefix = getattr(options, 'prefix', '')

        # TODO: add and handle 'all' option
        self.pagination = getattr(
            options, 'pagination', (15, 20, 30, 50, 100))
        self.default_slice_length = getattr(options, 'default_slice_length', 15)

        # Query args
        self.filter_arg = getattr(options, 'filter_arg', 'f')
        self.search_arg = getattr(options, 'search_arg', 'q')
        self.order_by_arg = getattr(options, 'order_by_arg', 'sort')
        self.slice_start_arg = getattr(options, 'slice_start_arg', 'start')
        self.slice_length_arg = getattr(options, 'slice_length_arg', 'length')


class DeclarativeColumnsMetaclass(type):
    '''
    Metaclass that converts `.Column` objects defined on a class to the
    dictionary `.Table.base_columns`, taking into account parent class
    `base_columns` as well.
    '''
    def __new__(mcs, name, bases, attrs):
        attrs['_meta'] = TableOptions(attrs.get('Meta', None))

        dt2_attrs = {
            'Meta': attrs.get('Meta', type('Meta', (object,), {})),
        }

        if hasattr(dt2_attrs['Meta'], 'prefix'):
            dt2_attrs['Meta'].prefix += '_'

        # extract declared columns
        cols, remainder = [], {}
        for attr_name, attr in attrs.items():
            if isinstance(attr, columns.Column):
                cols.append((attr_name, attr))
            else:
                remainder[attr_name] = attr
                if attr_name.startswith('render_'):
                    dt2_attrs[attr_name] = attr

        attrs = remainder

        # TODO: do not rely on django_tables2 for ordering
        cols.sort(key=lambda x: x[1].dt2_column.creation_counter)

        # If this class is subclassing other tables, add their fields as
        # well. Note that we loop over the bases in *reverse* - this is
        # necessary to preserve the correct order of columns.
        parent_columns = []
        for base in bases[::-1]:
            if hasattr(base, 'base_columns'):
                parent_columns = (list(base.base_columns.items()) +
                                  parent_columns)

        # Start with the parent columns
        base_columns = collections.OrderedDict(parent_columns)

        # Explicit columns override both parent and generated columns
        base_columns.update(collections.OrderedDict(cols))

        # Remove any columns from our remainder, else columns from our parent
        # class will remain
        for attr_name in remainder:
            if attr_name in base_columns:
                base_columns.pop(attr_name)

        # Set the ordering of django_tables2 columns exlicitly in order to get
        # correct order when subclassing comes into play
        if not hasattr(dt2_attrs['Meta'], 'sequence'):
            dt2_attrs['Meta'].sequence = list(base_columns.keys())

        # Add columns to the django_tables2 table
        for column_name, column in base_columns.items():
            dt2_attrs[column_name] = column.dt2_column

        # Construct type for the django_tables2 table
        attrs['dt2_table_type'] = type(name + '_dt2',
                                       (tables.Table,),
                                       dt2_attrs)

        attrs['base_columns'] = base_columns

        return super(DeclarativeColumnsMetaclass, mcs).__new__(
            mcs, name, bases, attrs)


Table = DeclarativeColumnsMetaclass('Table', (BaseTable,), {})
Table.__doc__ = BaseTable.__doc__
