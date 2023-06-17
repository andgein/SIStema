from django.utils.functional import cached_property

__all__ = ["ExcelColumn", "ExcelMultiColumn", "PlainExcelColumn", "LinkExcelColumn"]


class ExcelColumn:
    def __init__(self, name='', plain_header=True):
        self.name = name
        self.plain_header = plain_header

    @property
    def width(self):
        return 1

    @property
    def header_height(self):
        return 1

    @cached_property
    def header_format(self):
        return None

    @cached_property
    def cell_format(self):
        return None

    def write_header(self, sheet, irow, icol, header_height=None):
        if self.plain_header or header_height == 1:
            sheet.write(irow, icol, self.name, self.header_format)
        else:
            sheet.merge_range(irow,
                              icol,
                              irow + header_height - 1,
                              icol,
                              self.name,
                              cell_format=self.header_format)
        return irow + (1 if self.plain_header else header_height)

    def write(self, sheet, irow, icol, header_height=None):
        return NotImplementedError()


class PlainExcelColumn(ExcelColumn):
    def __init__(self,
                 data=None,
                 comments=None,
                 cell_width=15,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = [] if data is None else data
        self.comments = [] if comments is None else comments
        self.cell_width = cell_width

    def write(self, sheet, irow, icol, header_height=None):
        sheet.set_column(icol, icol, self.cell_width)

        irow = self.write_header(sheet, irow, icol, header_height)

        for i, value in enumerate(self.data):
            sheet.write(irow + i, icol, value, self.cell_format)
        for i, comment in enumerate(self.comments):
            if comment:
                sheet.write_comment(irow + i, icol, comment)


class LinkExcelColumn(PlainExcelColumn):
    def __init__(self, data_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_urls = self.data if data_urls is None else data_urls
        if len(self.data) != len(self.data_urls):
            raise ValueError()

    def write(self, sheet, irow, icol, header_height=None):
        sheet.set_column(icol, icol, self.cell_width)

        irow = self.write_header(sheet, irow, icol, header_height)

        for i, (value, url) in enumerate(zip(self.data, self.data_urls)):
            if url:
                sheet.write_url(irow + i, icol, url, string=str(value))
            else:
                sheet.write(irow + i, icol, value)


class ExcelMultiColumn(ExcelColumn):
    def __init__(self, subcolumns=None, *args, **kwargs):
        if not subcolumns:
            raise ValueError(
                'ExcelMultiColumn should have at least one subcolumn')
        self.subcolumns = subcolumns
        super().__init__(*args, **kwargs)

    @property
    def width(self):
        return sum(subcolumn.width for subcolumn in self.subcolumns)

    @property
    def header_height(self):
        return 1 + max(subcolumn.header_height
                       for subcolumn in self.subcolumns)

    def write(self, sheet, irow, icol, header_height=None):
        if not self.plain_header:
            if len(self.subcolumns) > 1:
                sheet.merge_range(irow,
                                  icol,
                                  irow,
                                  icol + self.width - 1,
                                  self.name,
                                  self.header_format)
            else:
                sheet.write(irow, icol, self.name, self.header_format)
            irow += 1

        for column in self.subcolumns:
            column.header_format = self.header_format
            column.write(sheet, irow, icol, header_height=header_height - 1)
            icol += column.width
