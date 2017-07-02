from django.contrib import admin

import sistema.admin

from . import models


@admin.register(models.EntranceExamScorer)
class EntranceExamScorerAdmin(sistema.admin.ModelAdmin):
    list_display = ('id', 'name', 'max_level')


@admin.register(models.ProgramTaskScore)
class ProgramTaskScoreAdmin(sistema.admin.ModelAdmin):
    list_display = ('id', 'scorer', 'task', 'score')


@admin.register(models.TestCountScore)
class TestCountScoreAdmin(sistema.admin.ModelAdmin):
    list_display = ('id', 'scorer', 'count', 'score')
