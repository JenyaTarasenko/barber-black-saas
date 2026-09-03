import uuid
from django.db import models

# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon
# pyrefly: ignore [missing-import]
from apps.branch.models import Branch



class Employee(models.Model):
    """
    Сотрудник салона.

    Employee — это сотрудник бизнеса,
    а не обязательно пользователь системы.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="employees",
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
        db_table = "employees"

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()



class EmployeeBranch(models.Model):
    """
    Связь сотрудника с филиалом.

    Один сотрудник может работать в нескольких филиалах.
    Один филиал может иметь нескольких сотрудников.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employee_branches",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="employee_branches",
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
        db_table = "employee_branches"

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "branch"],
                name="unique_employee_branch",
            ),
        ]

    def __str__(self):
        return f"{self.employee} → {self.branch}"
