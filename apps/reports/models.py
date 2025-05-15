from django.conf import settings
from django.db import models

from vagvin.models import BaseModel


class Query(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='queries',
                             verbose_name="Пользователь")
    vin = models.CharField(max_length=17, verbose_name="VIN-номер")
    query_type = models.CharField(max_length=50, verbose_name="Тип отчёта")

    class Meta:
        verbose_name = "Запрос"
        verbose_name_plural = "Запросы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vin} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"
