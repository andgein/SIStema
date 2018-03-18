from django.contrib import admin
from polymorphic.admin import (PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter,
                               PolymorphicInlineSupportMixin,
                               StackedPolymorphicInline)

import sistema.polymorphic

from . import models


@admin.register(models.Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'filename')
    search_fields = ('name', )
    list_display_links = ('id', 'name')


@admin.register(models.FontFamily)
class FontFamilyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'normal', 'bold', 'italic', 'bold_italic')
    search_fields = ('name', )
    list_display_links = ('id', 'name')


@admin.register(models.ParagraphStyle)
class ParagraphStyleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'leading',
        'alignment',
        'font',
        'font_size',
        'bullet_font',
        'space_before',
        'space_after',
        'left_indent',
    )
    search_fields = ('name', )


class AbstractTableStyleCommandInline(StackedPolymorphicInline):
    class CellFormattingTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.CellFormattingTableStyleCommand

    class FontTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.FontTableStyleCommand

    class LeadingTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.LeadingTableStyleCommand

    class TextColorTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.TextColorTableStyleCommand

    class AlignmentTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.AlignmentTableStyleCommand

    class PaddingTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.PaddingTableStyleCommand

    class ValignTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.ValignTableStyleCommand

    class LineTableStyleCommandInline(StackedPolymorphicInline.Child):
        model = models.LineTableStyleCommand

    model = models.AbstractTableStyleCommand
    child_inlines = (
       CellFormattingTableStyleCommandInline,
       FontTableStyleCommandInline,
       LeadingTableStyleCommandInline,
       TextColorTableStyleCommandInline,
       AlignmentTableStyleCommandInline,
       PaddingTableStyleCommandInline,
       ValignTableStyleCommandInline,
       LineTableStyleCommandInline,
    )


@admin.register(models.AbstractDocumentBlock)
class AbstractDocumentBlockAdmin(
        sistema.polymorphic.PolymorphicParentModelAdmin
):
    base_model = models.AbstractDocumentBlock
    list_display = ('id', 'document', 'order')
    list_filter = ('document', PolymorphicChildModelFilter)
    ordering = ('-document', 'order')


@admin.register(models.Paragraph)
@admin.register(models.PageBreak)
@admin.register(models.Spacer)
@admin.register(models.Image)
class AbstractDocumentBlockChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.AbstractDocumentBlock


class TableRowInline(admin.TabularInline):
    model = models.TableRow
    extra = 0
    show_change_link = True
    ordering = ('order',)


@admin.register(models.Table)
class TableAdmin(PolymorphicInlineSupportMixin, PolymorphicChildModelAdmin):
    base_model = models.AbstractDocumentBlock
    inlines = (TableRowInline, AbstractTableStyleCommandInline)


class TableCellInline(admin.TabularInline):
    model = models.TableCell
    extra = 0
    show_change_link = True
    ordering = ('order',)


@admin.register(models.TableRow)
class TableRowAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'order')
    list_filter = ('table', )
    ordering = ('table', 'order')
    inlines = (TableCellInline,)


@admin.register(models.TableCell)
class TableCellAdmin(admin.ModelAdmin):
    list_display = ('id', 'row', 'order')
    list_filter = ('row__table', 'row',)
    ordering = ('row__table', 'row', 'order')


class AbstractDocumentBlockInline(StackedPolymorphicInline):
    class ParagraphInline(StackedPolymorphicInline.Child):
        model = models.Paragraph

    class PageBreakInline(StackedPolymorphicInline.Child):
        model = models.PageBreak

    class SpacerInline(StackedPolymorphicInline.Child):
        model = models.Spacer

    class ImageInline(StackedPolymorphicInline.Child):
        model = models.Image

    class TableInline(StackedPolymorphicInline.Child):
        model = models.Table
        show_change_link = True

    model = models.AbstractDocumentBlock
    child_inlines = (
        ParagraphInline,
        PageBreakInline,
        SpacerInline,
        ImageInline,
        TableInline,
    )
    ordering = ('order',)


@admin.register(models.Document)
class DocumentAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'page_size')
    inlines = (AbstractDocumentBlockInline,)
    search_fields = ('=id', 'name')
