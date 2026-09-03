import uuid

from django.db import models

# pyrefly: ignore [missing-import]
from apps.branch.models import Branch
# pyrefly: ignore [missing-import]
from apps.employee.models import Employee


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
        related_name="schedules",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="schedules",
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

    class Meta:
        db_table = "schedules"

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "branch", "weekday"],
                name="unique_employee_branch_weekday_schedule",
            ),
        ]

    def __str__(self):
        return (
            f"{self.employee} — "
            f"{self.branch} — "
            f"{self.get_weekday_display()}"
        )


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