from django.contrib import admin

from . import models


@admin.register(models.EntranceExamScorer)
class EntranceExamScorerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'max_level')


@admin.register(models.ProgramTaskScore)
class ProgramTaskScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'scorer', 'task', 'score')


@admin.register(models.TestCountScore)
class TestCountScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'scorer', 'count', 'score')

