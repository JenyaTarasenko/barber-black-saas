import uuid
from django.conf import settings
from django.db import models    
# pyrefly: ignore [missing-import]
from apps.branch.models import Branch
# pyrefly: ignore [missing-import]
from apps.clients.models import Client
# pyrefly: ignore [missing-import]
from apps.employee.models import Employee
# pyrefly: ignore [missing-import]
from apps.services.models import Service
# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon


class Appointment(models.Model):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    STATUS_CHOICES = [
        (CREATED, "Created"),
        (CONFIRMED, "Confirmed"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
        (NO_SHOW, "No Show"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    salon = models.ForeignKey(
        Salon,
        on_delete=models.CASCADE,
        related_name="appointments",
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    start_datetime = models.DateTimeField()

    end_datetime = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=CREATED,
    )

    client_notes = models.TextField(
        blank=True,
    )

    internal_notes = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_appointments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "appointments"
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.client} — {self.start_datetime}"


class AppointmentService(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="appointment_services",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointment_services",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    duration_minutes = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "appointment_services"

    def __str__(self):
        return f"{self.appointment} — {self.service}"


class AppointmentStatusHistory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    status = models.CharField(
        max_length=20,
        choices=Appointment.STATUS_CHOICES,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment_status_changes",
    )

    comment = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "appointment_status_history"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.appointment} — {self.status}"
