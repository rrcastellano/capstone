from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.index, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('contact-us/', views.contact, name='contact'),
    path('recharge/', views.recharge, name='recharge'),
    path('bulk-recharge/', views.bulk_recharge, name='bulk_recharge'),
    path('history/', views.manage_recharges, name='manage_recharges'),
    path('edit-recharge/<int:pk>/', views.edit_recharge, name='edit_recharge'),
    path('delete-recharge/<int:pk>/', views.delete_recharge, name='delete_recharge'),
    path('delete-all-recharges/', views.delete_all_recharges, name='delete_all_recharges'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API Endpoints
    path('api/auth/login/', api_views.api_login, name='api_login'),
    path('api/auth/logout/', api_views.api_logout, name='api_logout'),
    path('api/settings/', api_views.api_settings, name='api_settings'),
    path('api/recharges/', api_views.api_recharge_list, name='api_recharge_list'),
    path('api/recharges/<int:pk>/', api_views.api_recharge_detail, name='api_recharge_detail'),
    path('api/recharges/monthly/', views.api_recharges_monthly, name='api_recharges_monthly'),
    path('settings/', views.settings_view, name='settings'),
]
