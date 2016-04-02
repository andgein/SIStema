from django.contrib import admin

from . import models


class EntranceUserUpgradeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'for_school',
    )

admin.site.register(models.TestEntranceExamTask)
admin.site.register(models.FileEntranceExamTask)
admin.site.register(models.ProgramEntranceExamTask)
admin.site.register(models.EntranceExam)

admin.site.register(models.EntranceLevel)
admin.site.register(models.EntranceStep)

admin.site.register(models.EntranceExamTaskSolution)
admin.site.register(models.ProgramEntranceExamTaskSolution)

admin.site.register(models.EntranceUserUpgrade, EntranceUserUpgradeAdmin)
