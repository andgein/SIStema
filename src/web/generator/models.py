import functools

import djchoices
import polymorphic.models
import relativefilepathfield.fields
from django.db import models
import django.db.migrations.writer
from relativefilepathfield.fields import RelativeFilePathField
from django.conf import settings

import reportlab.lib.enums
import reportlab.lib.pagesizes
import reportlab.lib.styles
import reportlab.lib.colors
import reportlab.pdfbase.pdfmetrics
import reportlab.pdfbase.ttfonts
import reportlab.platypus.tables


class Alignment(djchoices.DjangoChoices):
    JUSTIFY = djchoices.ChoiceItem(reportlab.lib.enums.TA_JUSTIFY, 'Justify')
    LEFT = djchoices.ChoiceItem(reportlab.lib.enums.TA_LEFT, 'Left')
    RIGHT = djchoices.ChoiceItem(reportlab.lib.enums.TA_RIGHT, 'Right')
    CENTER = djchoices.ChoiceItem(reportlab.lib.enums.TA_CENTER, 'Center')


class TableCellAlignment(djchoices.DjangoChoices):
    LEFT = djchoices.ChoiceItem()
    RIGHT = djchoices.ChoiceItem()
    CENTER = djchoices.ChoiceItem()
    DECIMAL = djchoices.ChoiceItem()


# See reportlab.lib.colors for all available colors
class Color(djchoices.DjangoChoices):
    BLACK = djchoices.ChoiceItem(reportlab.lib.colors.black.hexval(), 'Black')
    WHITE = djchoices.ChoiceItem(reportlab.lib.colors.white.hexval(), 'White')
    RED = djchoices.ChoiceItem(reportlab.lib.colors.red.hexval(), 'Red')
    GREEN = djchoices.ChoiceItem(reportlab.lib.colors.green.hexval(), 'Green')
    BLUE = djchoices.ChoiceItem(reportlab.lib.colors.blue.hexval(), 'Blue')
    YELLOW = djchoices.ChoiceItem(reportlab.lib.colors.yellow.hexval(),
                                  'Yellow')
    CYAN = djchoices.ChoiceItem(reportlab.lib.colors.cyan.hexval(), 'Cyan')
    MAGENTA = djchoices.ChoiceItem(reportlab.lib.colors.magenta.hexval(),
                                   'Magenta')
    BROWN = djchoices.ChoiceItem(reportlab.lib.colors.brown.hexval(), 'Brown')


class PageSize(djchoices.DjangoChoices):
    A6 = djchoices.ChoiceItem()
    A5 = djchoices.ChoiceItem()
    A4 = djchoices.ChoiceItem()
    A3 = djchoices.ChoiceItem()
    A2 = djchoices.ChoiceItem()
    A1 = djchoices.ChoiceItem()
    A0 = djchoices.ChoiceItem()

    LETTER = djchoices.ChoiceItem(label='Letter')
    LEGAL = djchoices.ChoiceItem(label='Legal')
    ELEVEN_SEVENTEEN = djchoices.ChoiceItem(label='11x17')

    B6 = djchoices.ChoiceItem()
    B5 = djchoices.ChoiceItem()
    B4 = djchoices.ChoiceItem()
    B3 = djchoices.ChoiceItem()
    B2 = djchoices.ChoiceItem()
    B1 = djchoices.ChoiceItem()
    B0 = djchoices.ChoiceItem()

    @classmethod
    def get_pagesize(cls, page_size_str):
        return getattr(reportlab.lib.pagesizes, page_size_str)


class ProcessedByVisitor:
    def _process_by_visitor(self, visitor=None):
        if visitor is not None:
            visitor.visit(self)


class Font(models.Model):
    name = models.CharField(max_length=100, unique=True)

    filename = RelativeFilePathField(
        path=django.db.migrations.writer.SettingsReference(
            settings.SISTEMA_GENERATOR_FONTS_DIR,
            'SISTEMA_GENERATOR_FONTS_DIR'
        ),
        match='.*\.ttf',
        recursive=True,
        max_length=1000)

    def __str__(self):
        return self.name

    def get_reportlab_font(self):
        return reportlab.pdfbase.ttfonts.TTFont(self.name,
                                                self.get_filename_abspath())

    def register_in_reportlab(self):
        reportlab.pdfbase.pdfmetrics.registerFont(self.get_reportlab_font())

    _registered = False

    @classmethod
    def register_all_in_reportlab(cls):
        if cls._registered:
            return
        cls._registered = True

        for font in cls.objects.all():
            font.register_in_reportlab()


class FontFamily(models.Model):
    name = models.CharField(max_length=100, unique=True)

    normal = models.ForeignKey(
        Font,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text='Обычное начертание',
        related_name='+',
    )

    bold = models.ForeignKey(
        Font,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text='Полужирное начертание',
        related_name='+',
    )

    italic = models.ForeignKey(
        Font,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text='Курсивное начертание',
        related_name='+',
    )

    bold_italic = models.ForeignKey(
        Font,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text='Полужирное курсивное начертание',
        related_name='+',
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Font families'

    def register_in_reportlab(self):
        # Ensure that all fonts are registered
        Font.register_all_in_reportlab()

        reportlab.pdfbase.pdfmetrics.registerFontFamily(self.name,
                                                        self.normal.name,
                                                        self.bold.name,
                                                        self.italic.name,
                                                        self.bold_italic.name)

    _registered = False

    @classmethod
    def register_all_in_reportlab(cls):
        if cls._registered:
            return
        cls._registered = True

        for family in cls.objects.all():
            family.register_in_reportlab()


class ParagraphStyle(models.Model):
    name = models.CharField(max_length=100)

    leading = models.FloatField()

    alignment = models.PositiveIntegerField(
        choices=Alignment.choices,
        validators=[Alignment.validator],
    )

    font = models.ForeignKey(
        Font,
        on_delete=models.CASCADE,
        related_name='+',
    )

    font_size = models.PositiveIntegerField()

    bullet_font = models.ForeignKey(
        Font,
        on_delete=models.CASCADE,
        related_name='+',
    )

    space_before = models.PositiveIntegerField()

    space_after = models.PositiveIntegerField()

    left_indent = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    def get_reportlab_style(self):
        return reportlab.lib.styles.ParagraphStyle(
            name=self.name,
            leading=self.leading,
            fontName=self.font.name,
            fontSize=self.font_size,
            bulletFontName=self.bullet_font.name,
            alignment=self.alignment,
            spaceBefore=self.space_before,
            spaceAfter=self.space_after,
            leftIndent=self.left_indent,
        )


class Document(models.Model):
    name = models.CharField(
        max_length=255,
        help_text='Не показывается школьникам. Например, «Договор 2016 с '
                  'Берендеевыми Полянами»',
    )

    page_size = models.CharField(max_length=20,
                                 choices=PageSize.choices,
                                 validators=[PageSize.validator])

    left_margin = models.IntegerField(default=0)

    right_margin = models.IntegerField(default=0)

    top_margin = models.IntegerField(default=0)

    bottom_margin = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class AbstractDocumentBlock(polymorphic.models.PolymorphicModel,
                            ProcessedByVisitor):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name='blocks',
    )

    order = models.PositiveIntegerField(
        help_text='Блоки выстраиваются по возрастанию порядка',
    )

    class Meta:
        verbose_name = 'document block'
        unique_together = ('document', 'order')
        ordering = ('document', 'order')

    def get_reportlab_block(self, visitor=None):
        raise NotImplementedError(
            'Child should implement its own get_reportlab_block()')


class Paragraph(AbstractDocumentBlock):
    text = models.TextField()

    style = models.ForeignKey(ParagraphStyle, on_delete=models.CASCADE)

    bulletText = models.TextField(default=None, null=True, blank=True)

    def __str__(self):
        return self.text[:80]

    def get_reportlab_block(self, visitor=None):
        self._process_by_visitor(visitor)
        return reportlab.platypus.Paragraph(self.text,
                                            self.style.get_reportlab_style(),
                                            self.bulletText)


class Spacer(AbstractDocumentBlock):
    width = models.PositiveIntegerField()

    height = models.PositiveIntegerField()

    is_glue = models.BooleanField(default=False)

    def __str__(self):
        return 'Spacer %dx%d' % (self.width, self.height)

    def get_reportlab_block(self, visitor=None):
        self._process_by_visitor(visitor)
        return reportlab.platypus.Spacer(self.width, self.height, self.is_glue)


class PageBreak(AbstractDocumentBlock):
    def get_reportlab_block(self, visitor=None):
        return reportlab.platypus.PageBreak()


class Image(AbstractDocumentBlock):
    filename = relativefilepathfield.fields.RelativeFilePathField(
        path=django.db.migrations.writer.SettingsReference(
            settings.SISTEMA_GENERATOR_ASSETS_DIR,
            'SISTEMA_GENERATOR_ASSETS_DIR',
        ),
        recursive=True
    )

    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        help_text='В пунктах. Оставьте пустым, чтобы взять размеры самой '
                  'картинки',
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        help_text='В пунктах. Оставьте пустым, чтобы взять размеры самой '
                  'картинки',
    )

    def get_reportlab_block(self, visitor=None):
        self._process_by_visitor(visitor)
        return reportlab.platypus.Image(
            self.get_filename_abspath(), width=self.width, height=self.height)


class Table(AbstractDocumentBlock):
    def get_reportlab_table_style(self):
        return reportlab.platypus.TableStyle(
            [s.get_reportlab_style_command() for s in self.style_commands.all()]
        )

    def get_reportlab_block(self, visitor=None):
        self._process_by_visitor(visitor)
        return reportlab.platypus.Table(
            [r.get_reportlab_row(visitor) for r in self.rows.order_by('order')],
            style=self.get_reportlab_table_style()
        )

    def __str__(self):
        return 'Table [%s] #%d ' % (self.document, self.order)


class TableRow(models.Model, ProcessedByVisitor):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='rows',
    )

    order = models.PositiveIntegerField(
        help_text='Строки упорядочиваются по возрастанию порядка')

    class Meta:
        ordering = ('table', 'order')
        unique_together = ('table', 'order')

    def __str__(self):
        return '%s[%d]' % (self.table, self.order)

    def get_reportlab_row(self, visitor):
        self._process_by_visitor(visitor)
        return [c.get_reportlab_block(visitor)
                for c in self.cells.order_by('order')]


class TableCell(models.Model, ProcessedByVisitor):
    row = models.ForeignKey(
        TableRow,
        on_delete=models.CASCADE,
        related_name='cells',
    )

    block = models.ForeignKey(
        AbstractDocumentBlock,
        on_delete=models.CASCADE,
        related_name='+',
    )

    order = models.PositiveIntegerField(
        help_text='Ячейки упорядочиваются по возрастанию порядка')

    class Meta:
        ordering = ('row', 'order')
        unique_together = ('row', 'order')

    def __str__(self):
        return '%s[%d]: %s' % (self.row, self.order, self.block)

    def get_reportlab_block(self, visitor):
        self._process_by_visitor(visitor)
        return self.block.get_reportlab_block(visitor)


# See page 79 of documentation
# (https://www.reportlab.com/docs/reportlab-userguide.pdf) for all available
# table style commands
# From this documentation:
#   The commands passed to TableStyles come in three main groups which affect
#   the table background, draw lines, or set cell styles.
#
#   The first element of each command is its identifier, the second and third
#   arguments determine the cell coordinates of the box of cells which are
#   affected with negative coordinates counting backwards from the limit values
#   as in Python indexing. The coordinates are given as (column, row) which
#   follows the spreadsheet 'A1' model, but not the more natural (for
#   mathematicians) 'RC' ordering. The top left cell is (0, 0) the bottom right
#   is (-1, -1). Depending on the command various extra (???) occur at indices
#   beginning at 3 on.
class AbstractTableStyleCommand(polymorphic.models.PolymorphicModel):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='style_commands',
    )

    start_column = models.IntegerField(
        default=0,
        help_text='Координаты начала: столбец',
    )

    start_row = models.IntegerField(
        default=0,
        help_text='Координаты начала: строка',
    )

    stop_column = models.IntegerField(
        default=-1,
        help_text='Координаты конца: столбец',
    )

    stop_row = models.IntegerField(
        help_text='Координаты конца: строка',
        default=-1,
    )

    class Meta:
        verbose_name = 'table style command'

    @property
    def start(self):
        return self.start_column, self.start_row

    @property
    def stop(self):
        return self.stop_column, self.stop_row

    @property
    def params(self):
        # param can be dotted path to the nested attribute, i.e. "font.name".
        # In this case we need get self.font.name, so we split param by "." and apply
        # functools.reduce with getattr
        return [
            functools.reduce(getattr, [self] + param.split('.')) for param in self.command_params
        ]

    def __str__(self):
        return '%s[%s:%s].%s(%s)' % (
            self.table,
            self.start,
            self.stop,
            self.command_name,
            ', '.join(map(str, self.params)),
        )

    def get_reportlab_style_command(self):
        return (self.command_name, self.start, self.stop) + tuple(self.params)


class CellFormattingTableStyleCommand(AbstractTableStyleCommand):
    command_name = '<UNKNOWN>'

    command_params = []


class FontTableStyleCommand(CellFormattingTableStyleCommand):
    command_name = 'FONT'

    command_params = ['font.name', 'size']

    font = models.ForeignKey(Font, on_delete=models.CASCADE)

    size = models.PositiveIntegerField(null=True, default=None, blank=True)


class LeadingTableStyleCommand(CellFormattingTableStyleCommand):
    command_name = 'LEADING'

    command_params = ['leading']

    leading = models.PositiveIntegerField(help_text='В пунктах')


class TextColorTableStyleCommand(CellFormattingTableStyleCommand):
    command_name = 'TEXTCOLOR'

    command_params = ['color']

    color = models.CharField(
        max_length=20, choices=Color.choices, validators=[Color.validator])


class AlignmentTableStyleCommand(CellFormattingTableStyleCommand):
    command_name = 'ALIGNMENT'

    command_params = 'align'

    align = models.CharField(max_length=20,
                             choices=TableCellAlignment.choices,
                             validators=[TableCellAlignment.validator])


class PaddingTableStyleCommand(CellFormattingTableStyleCommand):
    command_params = ['padding']

    direction = models.CharField(max_length=6, choices=[('LEFT', 'Left'),
                                                        ('RIGHT', 'Right'),
                                                        ('BOTTOM', 'Bottom'),
                                                        ('TOP', 'Top')
                                                        ])

    padding = models.PositiveIntegerField(help_text='В пунктах')

    @property
    def command_name(self):
        return '%sPADDING' % (self.direction,)


# TODO: Background commands: BACKGROUND, ROWBACKGROUNDS, COLBACKGROUNDS


class ValignTableStyleCommand(CellFormattingTableStyleCommand):
    command_name = 'VALIGN'

    command_params = ['direction']

    direction = models.CharField(max_length=6, choices=[('TOP', 'Top'),
                                                        ('MIDDLE', 'Middle'),
                                                        ('BOTTOM', 'Bottom')])


class LineTableStyleCommand(AbstractTableStyleCommand):
    command_name = models.CharField(
        max_length=100,
        choices=[
            (c, c.title())
            for c in sorted(reportlab.platypus.tables.LINECOMMANDS)
        ],
    )

    command_params = ['thickness', 'color']

    thickness = models.FloatField(help_text='В пунктах')

    color = models.CharField(
        max_length=20, choices=Color.choices, validators=[Color.validator])

    def get_reportlab_command(self):
        return (self.command_name,
                self.start, self.stop,
                self.thickness,
                reportlab.lib.colors.HexColor(self.color))
