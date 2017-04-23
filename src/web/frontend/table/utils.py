import csv

import django.http.response

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
        self.export_format = None

    def configure(self, table):
        if table.exportable:
            export = self.request.GET.get(table.export_arg)
            try:
                self.export_format = table.ExportFormat(export)
            except ValueError:
                pass

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

        # Pagination
        if self.export_format is None:
            # Paginate only if not exporting
            slice_length = self.request.GET.get(table.slice_length_arg)
            try:
                slice_length = int(slice_length)
            except (ValueError, TypeError):
                slice_length = None

            if slice_start is not None or slice_length is not None:
                table.slice(slice_start, slice_length)

        return self


class TableDataSource:
    def __init__(self, table):
        self.table = table

    def get_response(self, request):
        config = RequestConfig(request).configure(self.table)
        rows = self.table.as_plain_rows()
        column_names = self.table.columns.keys()

        if config.export_format is None:
            return django.http.response.JsonResponse({
                'data': rows,
                'recordsTotal': self.table.initial_qs.count(),
                'recordsFiltered': self.table.filtered_qs.count(),
            })

        # TODO: understand, how to correctly export columns containing HTML
        if config.export_format == self.table.ExportFormat.CSV:
            response = django.http.response.HttpResponse(
                content_type='text/csv')
            # TODO: configure export file name in table
            response['Content-Disposition'] = 'attachment; filename="table.csv"'
            csv_writer = csv.writer(response)
            csv_writer.writerow(column_names)
            for row in rows:
                csv_writer.writerow(row[name] for name in column_names)

            return response

        raise django.http.Http404
