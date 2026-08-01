from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from .models import Recharge, Settings, ContactLog

# Unregister User to register our custom version
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login', 'recharge_count')
    list_filter = BaseUserAdmin.list_filter + ('last_login',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(recharge_count=Count('recharge'))
        return queryset

    def recharge_count(self, obj):
        return obj.recharge_count
    recharge_count.short_description = _("Nº Recargas")
    recharge_count.admin_order_field = 'recharge_count'

@admin.register(ContactLog)
class ContactLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome', 'status', 'data_envio', 'short_message')
    list_filter = ('status', 'data_envio')
    search_fields = ('nome', 'email', 'mensagem')
    readonly_fields = ('data_envio',)
    ordering = ('-data_envio',)

    def short_message(self, obj):
        return obj.mensagem[:50] + "..." if len(obj.mensagem) > 50 else obj.mensagem
    short_message.short_description = _("Mensagem")

@admin.register(Recharge)
class RechargeAdmin(admin.ModelAdmin):
    list_display = ('user', 'data', 'kwh', 'custo', 'isento', 'local')
    list_filter = ('user', 'isento', 'data')
    search_fields = ('user__username', 'local', 'observacoes')
    date_hierarchy = 'data'

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'preco_gasolina', 'consumo_km_l')
    search_fields = ('user__username',)
