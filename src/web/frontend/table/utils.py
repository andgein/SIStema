import django_tables2.utils

class Accessor(django_tables2.utils.Accessor):
    @property
    def django_lookup(self):
        return '__'.join(self.bits)


A = Accessor


class RequestConfig:
    """
    Allows to configure table using request GET arguments, defined by table

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


# TODO: I don't like this class. Can we do that better?
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
