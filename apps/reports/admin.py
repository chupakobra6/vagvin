from django.contrib import admin
from .models import Query


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vin', 'query_type', 'created_at')
    list_filter = ('query_type', 'created_at')
    search_fields = ('vin', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'vin')
        }),
        ('Параметры отчета', {
            'fields': ('query_type',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at')
        }),
    )
