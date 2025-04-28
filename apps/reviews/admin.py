from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'email', 'approved', 'created_at')
    list_filter = ('approved', 'rating')
    search_fields = ('name', 'email', 'text')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews']
    list_editable = ['approved']
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'rating', 'text')
        }),
        ('Модерация', {
            'fields': ('approved', 'admin_response')
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_reviews(self, request, queryset):
        queryset.update(approved=True)
        self.message_user(request, f"{queryset.count()} отзывов одобрено")

    approve_reviews.short_description = "Одобрить выбранные отзывы"
