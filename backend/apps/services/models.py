import uuid

from django.db import models

# pyrefly: ignore [missing-import]
from apps.employee.models import Employee
# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon


class ServiceCategory(models.Model):
    """
    Категория услуг салона.

    Например:
    - Стрижки
    - Борода
    - Окрашивание
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="service_categories",
    )

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField(
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
        db_table = "service_categories"

    def __str__(self):
        return self.name


class Service(models.Model):
    """
    Конкретная услуга салона.

    Например:
    - Мужская стрижка
    - Детская стрижка
    - Коррекция бороды
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="services",
    )

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
    )

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    duration_minutes = models.PositiveIntegerField()

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
        db_table = "services"

    def __str__(self):
        return self.name


class EmployeeService(models.Model):
    """
    Связь между сотрудником и услугой.

    Определяет, какие услуги оказывает конкретный мастер.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employee_services",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="employee_services",
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
        db_table = "employee_services"

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "service"],
                name="unique_employee_service",
            ),
        ]

    def __str__(self):
        return f"{self.employee} → {self.service}"