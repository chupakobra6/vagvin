from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin that includes our custom fields"""
    list_display = ('username', 'email', 'balance', 'overdraft', 'created_at', 'referral_code', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'referral_code')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'additional_emails')}),
        ('Financials', {'fields': ('balance', 'overdraft')}),
        ('Referral System', {'fields': ('referral', 'referral_code')}),
        ('Dates', {'fields': ('created_at', 'updated_at', 'last_password_reset', 'last_login')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'referral_code'),
        }),
    )
