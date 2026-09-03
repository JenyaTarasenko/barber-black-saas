from django.core.exceptions import ValidationError
import uuid

from django.db import models

# pyrefly: ignore [missing-import]
from apps.branch.models import Branch
# pyrefly: ignore [missing-import]
from apps.employee.models import Employee

# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon

class Schedule(models.Model):
    """
    Рабочий график сотрудника в конкретном филиале.

    Один Schedule описывает рабочий день:
    например, понедельник 09:00 - 18:00.
    """

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    WEEKDAY_CHOICES = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employee_schedules",
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="salon_schedules",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="branch_schedules",
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAY_CHOICES,
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        super().clean()
        # Проверка 1: Employee принадлежит тому же Salon
        if self.employee_id and self.salon_id:
            if self.employee.salon_id != self.salon_id:
                raise ValidationError({
                    'employee': 'Employee belongs to a different salon than the schedule.'
                })

        # Проверка 2: Branch принадлежит тому же Salon
        if self.branch_id and self.salon_id:
            if self.branch.salon_id != self.salon_id:
                raise ValidationError({
                    'branch': 'Branch belongs to a different salon than the schedule.'
                })

        # Проверка 3: Employee и Branch между собой из одного Salon
        if self.employee_id and self.branch_id:
            if self.employee.salon_id != self.branch.salon_id:
                raise ValidationError({
                    'branch': 'Employee and Branch must belong to the same salon.'
                })

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'End time must be after start time.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.branch} — {self.get_weekday_display()}"

    class Meta:
        db_table = "schedules"

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "branch", "weekday"],
                name="unique_employee_branch_weekday_schedule",
            ),
        ]

 


class ScheduleBreak(models.Model):
    """
    Перерыв сотрудника внутри рабочего графика.

    Например:
    Schedule: 09:00 - 18:00
    Break:    13:00 - 14:00
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="breaks",
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:
        db_table = "schedule_breaks"

    def __str__(self):
        return (
            f"{self.schedule} — "
            f"{self.start_time} - {self.end_time}"
        )

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'Break end time must be after start time.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)