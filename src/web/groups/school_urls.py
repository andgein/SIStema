from django.urls import path

from groups.staff import views as staff_views

app_name = 'groups'


urlpatterns = [
    path('', staff_views.groups_list, name='list'),
    path('data/', staff_views.groups_list_data, name='list_data'),

    path('<str:group_name>/', staff_views.group_info, name='group'),
    path('<str:group_name>/members/data/', staff_views.members_data, name='members_data'),
    path('<str:group_name>/export/', staff_views.ExportGroup.as_view(), name='export_group'),
]
