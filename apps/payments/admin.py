from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'provider', 'amount', 'total_amount', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('user__username', 'user__email', 'invoice_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('invoice_id', 'created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'provider', 'status', 'invoice_id')
        }),
        ('Финансовая информация', {
            'fields': ('amount', 'total_amount')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at')
        }),
    ) 