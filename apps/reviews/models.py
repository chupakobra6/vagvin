from django.db import models
from vagvin.models import BaseModel

class Review(BaseModel):
    RATING_CHOICES = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]

    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(help_text='Не будет отображаться на сайте', verbose_name='Email')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5, verbose_name='Оценка')
    text = models.TextField(verbose_name='Текст отзыва')
    admin_response = models.TextField(blank=True, null=True, verbose_name='Ответ администратора')
    approved = models.BooleanField(default=False, verbose_name='Одобрен')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.rating}★"
