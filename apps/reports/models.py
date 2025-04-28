from django.conf import settings
from django.db import models

from vagvin.models import BaseModel


# TODO: Реализовать базовую модель для всех моделей проекта, где нужен BaseModel с created_at и updated_at
class Query(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='queries',
                             verbose_name="Пользователь")
    vin = models.CharField(max_length=17, verbose_name="VIN-номер")
    marka = models.CharField(max_length=100, blank=True, verbose_name="Марка/модель")
    tip = models.CharField(max_length=50, verbose_name="Тип отчёта")
    lang = models.CharField(max_length=10, default="ru", verbose_name="Язык отчёта")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Стоимость")

    class Meta:
        verbose_name = "Запрос"
        verbose_name_plural = "Запросы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vin} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"
