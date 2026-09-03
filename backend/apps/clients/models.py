import uuid

from django.db import models

# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon


class LoyaltyLevel(models.Model):
    """
    Уровень лояльности клиента конкретного салона.

    Например:
    Новый клиент → 0 визитов → 0%
    Постоянный → 5 визитов → 5%
    VIP → 20 визитов → 10%
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="loyalty_levels",
    )

    name = models.CharField(
        max_length=100,
    )

    min_visits = models.PositiveIntegerField(
        default=0,
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "loyalty_levels"

        constraints = [
            models.UniqueConstraint(
                fields=["salon", "name"],
                name="unique_salon_loyalty_level_name",
            ),
        ]

    def __str__(self):
        return self.name


class Client(models.Model):
    """
    Клиент конкретного салона.

    Клиент не является User.
    Он может записаться через публичную страницу
    без регистрации в системе.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="clients",
    )

    loyalty_level = models.ForeignKey(
        LoyaltyLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    phone = models.CharField(
        max_length=32,
    )

    email = models.EmailField(
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "clients"

        constraints = [
            models.UniqueConstraint(
                fields=["salon", "phone"],
                name="unique_salon_client_phone",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()