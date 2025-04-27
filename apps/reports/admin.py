from django.contrib import admin
from .models import Query


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vin', 'marka', 'tip', 'cost', 'created_at')
    list_filter = ('tip', 'lang', 'created_at')
    search_fields = ('vin', 'marka', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'vin', 'marka')
        }),
        ('Параметры отчета', {
            'fields': ('tip', 'lang', 'cost')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at')
        }),
    )
