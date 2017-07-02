import sistema.admin


class AbstractHomePageBlockAdmin(sistema.admin.ModelAdmin):
    list_display = ('id', 'school', 'order')
    list_filter = ('school', )
