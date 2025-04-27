from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'balance', 'overdraft', 'created_at', 'referral_code', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'referral_code')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('email', 'additional_emails')}),
        ('Финансы', {'fields': ('balance', 'overdraft')}),
        ('Реферальная система', {'fields': ('referral', 'referral_code')}),
        ('Даты', {'fields': ('created_at', 'updated_at', 'last_password_reset', 'last_login')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
