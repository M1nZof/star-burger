from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=255,
        unique=True,
        blank=True,
    )
    latitude = models.FloatField(
        'широта',
        blank=True,
        null=True,
    )

    longitude = models.FloatField(
        'долгота',
        blank=True,
        null=True
    )
    request_date = models.DateField(
        'дата запроса координат',
        default=timezone.now,
    )

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        return self.address

