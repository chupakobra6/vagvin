from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the User model"""
    list_display = ('username', 'email', 'display_balance', 'display_overdraft',
                   'display_referrals_count', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'referral_code')
    readonly_fields = ('referral_code', 'referral_link_display', 'last_password_reset')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Balance Information'), {'fields': ('balance', 'overdraft')}),
        (_('Referral Information'), {'fields': ('referral', 'referral_code', 'referral_link_display')}),
        (_('Additional Information'), {'fields': ('additional_emails', 'last_password_reset')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    def display_balance(self, obj):
        """Display balance with color based on value"""
        if obj.balance > 1000:
            color = 'green'
        elif obj.balance > 0:
            color = 'blue'
        else:
            color = 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{} ₽</span>', color, obj.balance)
    display_balance.short_description = 'Баланс'
    display_balance.admin_order_field = 'balance'
    
    def display_overdraft(self, obj):
        """Display overdraft with color"""
        if obj.overdraft > 0:
            return format_html('<span style="color: green; font-weight: bold;">{} ₽</span>', obj.overdraft)
        return '0 ₽'
    display_overdraft.short_description = 'Овердрафт'
    display_overdraft.admin_order_field = 'overdraft'
    
    def display_referrals_count(self, obj):
        """Display number of referrals"""
        count = obj.referrals.count()
        if count > 0:
            return format_html('<span style="font-weight: bold;">{}</span>', count)
        return '0'
    display_referrals_count.short_description = 'Рефералы'
    
    def referral_link_display(self, obj):
        """Display clickable referral link"""
        return format_html('<a href="http://vagvin.ru{}" target="_blank">{}</a>', 
                          obj.referral_link, obj.referral_link)
    referral_link_display.short_description = 'Реферальная ссылка'
