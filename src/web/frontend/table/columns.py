import itertools

import django_tables2 as tables

class BaseColumn:
    def __init__(self, verbose_name=''):
        self.verbose_name = verbose_name

    @property
    def header(self):
        return self.verbose_name


class Column(BaseColumn):
    dt2_class = tables.Column

    def __init__(self,
                 orderable=False,
                 order_by=(),
                 searchable=False,
                 search_in=(),
                 *args, **kwargs):
        super().__init__()

        self.orderable = True if order_by else orderable
        self.order_by = (order_by,) if isinstance(order_by, str) else order_by
        if self.orderable and not self.order_by:
            self.order_by = (kwargs['accessor'],)

        self.searchable = True if search_in else searchable
        self.search_in = ((search_in,) if isinstance(search_in, str)
                          else search_in)
        if self.searchable and not self.search_in:
            self.search_in = (kwargs['accessor'],)

        self.dt2_column = self.dt2_class(*args, orderable=False, **kwargs)

        render = getattr(self, 'render', None)
        if callable(render):
            self.dt2_column.render = render


    @property
    def accessor(self):
        return self.dt2_column.accessor

    @property
    def header(self):
        return self.dt2_column.header


class IndexColumn(Column):
    def __init__(self, *args, **kwargs):
        self.counter = itertools.count(1)
        super().__init__(
            empty_values=(),
            orderable=False,
            *args, **kwargs)

    def render(self):
        return str(next(self.counter))


class BooleanColumn(Column):
    dt2_class = tables.BooleanColumn


class CheckBoxColumn(Column):
    dt2_class = tables.CheckBoxColumn


class DateColumn(Column):
    dt2_class = tables.DateColumn


class DateTimeColumn(Column):
    dt2_class = tables.DateTimeColumn


class FileColumn(Column):
    dt2_class = tables.FileColumn


class LinkColumn(Column):
    dt2_class = tables.LinkColumn


class EmailColumn(Column):
    dt2_class = tables.EmailColumn


class URLColumn(Column):
    dt2_class = tables.URLColumn


class TemplateColumn(Column):
    dt2_class = tables.TemplateColumn
