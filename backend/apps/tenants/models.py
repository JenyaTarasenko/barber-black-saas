from django.db import models

import uuid

from django.conf import settings
from django.db import models


class Salon(models.Model):
    """
    Салон / бизнес-клиент SaaS.

    Salon является tenant'ом.
    Все основные бизнес-данные системы
    в дальнейшем будут привязаны к Salon.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=255,
    )

    slug = models.SlugField(
        unique=True,
        db_index=True,
    )

    phone = models.CharField(
        max_length=32,
        blank=True,
    )

    email = models.EmailField(
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
        db_table = "salons"

    def __str__(self):
        return self.name




class Role(models.Model):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    OWNER = "OWNER"
    BRANCH_ADMIN = "BRANCH_ADMIN"
    MASTER = "MASTER"

    ROLE_CHOICES = [
        (PLATFORM_ADMIN, "Platform Admin"),
        (OWNER, "Owner"),
        (BRANCH_ADMIN, "Branch Admin"),
        (MASTER, "Master"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        choices=ROLE_CHOICES,
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name
    

class SalonMembership(models.Model):
    """
    Связь пользователя с салоном и его ролью.

    Определяет:
    - к какому салону имеет доступ пользователь;
    - какую роль он имеет в этом салоне.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salon_memberships",
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="memberships",
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
        db_table = "salon_memberships"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "salon"],
                name="unique_user_salon_membership",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.salon.name} ({self.role.code})"
