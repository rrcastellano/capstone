from django.urls import path
from . import views

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
    path('api/recharges/monthly/', views.api_recharges_monthly, name='api_recharges_monthly'),
    path('settings/', views.settings_view, name='settings'),
]
