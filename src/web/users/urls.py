from django.urls import path, include

from users import views

urlpatterns = [
    path('accounts/settings/', views.account_settings, name='account_settings'),
    path('accounts/find-similar/', views.find_similar_accounts, name='account_find_similar'),
    path('accounts/', include('allauth.urls')),
    path('user/profile', views.profile, name='user-profile'),
]
