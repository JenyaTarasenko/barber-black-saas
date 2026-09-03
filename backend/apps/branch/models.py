from django.db import models
import uuid
# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon

class Branch(models.Model):
    """
    Филиал салона.

    Каждый Branch принадлежит одному Salon.
    Один Salon может иметь несколько Branch.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="branches",
    )

    name = models.CharField(
        max_length=255,
    )

    address = models.CharField(
        max_length=500,
        blank=True,
    )

    phone = models.CharField(
        max_length=32,
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
        db_table = "branches"

    def __str__(self):
        return f"{self.salon.name} — {self.name}"
