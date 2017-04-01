import django_tables2.utils

class Accessor(django_tables2.utils.Accessor):
    # TODO: is it possible to make accessor syntax similar to django queryset
    #       syntax?
    # SEPARATOR = '__'

    @property
    def django_lookup(self):
        return '__'.join(self.bits)


A = Accessor


# TODO(artemtab): should we allow comma-separated list of values for the order
#     argument?
class RequestConfig:
    """
    Allows to configure table using request GET arguments:
    - page: number of the page to show
    - per_page: how many rows to display on a single page
    - order: either <column_name> or -<column_name>
    - q: request for the global table search
    - q_<column name>: request for the specific column search
    - f_<column name>: comma-separated list of values to filter in specific
                       column

    If table has a prefix specified, then only the arguments with the same
    prefix will be used.
    """
    def __init__(self, request):
        self.request = request

    def configure(self, table):
        # TODO: Implement filtration

        # Global search
        query = self.request.GET.get(table.search_arg)
        if query is not None:
            table.search_by(query)

        # Column search
        for column_name in table.columns:
            arg = table.search_column_arg(column_name)
            query = self.request.GET.get(arg)
            if query is not None:
                table.search_by(query, column_name=column_name)

        # Ordering
        order_by = self.request.GET.getlist(table.order_by_arg)
        if order_by:
            # TODO: ignore not existing fields?
            table.order_by(*order_by)

        slice_start = self.request.GET.get(table.slice_start_arg)
        try:
            slice_start = int(slice_start)
        except (ValueError, TypeError):
            slice_start = None

        slice_length = self.request.GET.get(table.slice_length_arg)
        try:
            slice_length = int(slice_length)
        except (ValueError, TypeError):
            slice_length = None

        if slice_start is not None or slice_length is not None:
            table.slice(slice_start, slice_length)

        print(*self.request.GET.items(), sep='\n')


# TODO: I don't like this class
class DataTablesJsonView:
    def __init__(self, table):
        self.table = table

    def get_response_object(self, request):
        # TODO: draw argument
        return {
            'data': self.table.as_plain_rows(),
            'recordsTotal': self.table.initial_qs.count(),
            'recordsFiltered': self.table.filtered_qs.count(),
        }
