from django.contrib import admin
from django.utils.html import format_html

from .models import Payment
from .services import PaymentService


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""
    list_display = ('id', 'user_link', 'provider', 'amount', 'total_amount', 'status_badge', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('user__username', 'user__email', 'invoice_id')
    date_hierarchy = 'created_at'
    readonly_fields = ('invoice_id', 'created_at', 'updated_at', 'commission_amount')
    list_per_page = 20
    ordering = ('-created_at',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'provider', 'status', 'invoice_id')
        }),
        ('Финансовая информация', {
            'fields': ('amount', 'total_amount', 'commission_amount')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def user_link(self, obj):
        """Link to user admin."""
        url = f"/admin/auth/user/{obj.user.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.user)

    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user'

    def status_badge(self, obj):
        """Colored badge for status."""
        status_colors = {
            'pending': '#FFA500',
            'success': '#28a745',
            'failed': '#dc3545',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="padding: 4px 8px; border-radius: 4px; '
            'background-color: {}; color: white;">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    def commission_amount(self, obj):
        """Calculate commission amount."""
        return obj.commission_amount

    commission_amount.short_description = 'Комиссия'

    def has_delete_permission(self, request, obj=None):
        """Disable deletion of completed payments."""
        if obj and PaymentService.is_successful(obj):
            return False
        return super().has_delete_permission(request, obj)
