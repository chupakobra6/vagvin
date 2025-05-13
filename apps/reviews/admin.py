import logging

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Review

logger = logging.getLogger(__name__)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin configuration for Review model."""
    list_display = ('name', 'email', 'display_rating', 'created_at', 'approved', 'has_response')
    list_filter = ('approved', 'rating', 'created_at')
    search_fields = ('name', 'email', 'text', 'admin_response')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'unapprove_reviews']
    list_per_page = 20
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('name', 'email')
        }),
        ('Содержание отзыва', {
            'fields': ('rating', 'text')
        }),
        ('Модерация', {
            'fields': ('approved', 'admin_response')
        }),
        ('Дата и время', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def display_rating(self, obj: Review) -> str:
        """Display star rating with stars."""
        return f"{obj.rating} {'★' * obj.rating}{'☆' * (5 - obj.rating)}"

    display_rating.short_description = 'Оценка' 
    display_rating.admin_order_field = 'rating' 

    def has_response(self, obj: Review) -> bool:
        """Check if review has admin response."""
        return bool(obj.admin_response and obj.admin_response.strip())

    has_response.boolean = True 
    has_response.short_description = 'Ответ' 

    def approve_reviews(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Approve selected reviews."""
        updated = queryset.update(approved=True)
        logger.info(f"Admin {request.user} approved {updated} reviews")
        self.message_user(request, f"{updated} отзывов было одобрено.")

    approve_reviews.short_description = "Одобрить выбранные отзывы" 

    def unapprove_reviews(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Unapprove selected reviews."""
        updated = queryset.update(approved=False)
        logger.info(f"Admin {request.user} unapproved {updated} reviews")
        self.message_user(request, f"{updated} отзывов было скрыто.")

    unapprove_reviews.short_description = "Скрыть выбранные отзывы" 
