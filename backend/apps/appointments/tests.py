import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.tenants.models import Salon
from apps.clients.models import Client
from apps.employee.models import Employee
from apps.branch.models import Branch
from apps.services.models import Service, ServiceCategory
from apps.appointments.models import Appointment, AppointmentService, AppointmentStatusHistory

User = get_user_model()


class AppointmentBase(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.client = Client.objects.create(salon=self.salon, first_name="Alex", phone="+1")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")
        self.category = ServiceCategory.objects.create(salon=self.salon, name="C")
        self.service = Service.objects.create(
            salon=self.salon, category=self.category, name="S",
            price=Decimal("100"), duration_minutes=30,
        )
        self.user = User.objects.create_user(email="user@test.com", password="pass1234")

    def make_appointment(self, **kw):
        defaults = dict(
            salon=self.salon,
            client=self.client,
            employee=self.employee,
            branch=self.branch,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=1),
        )
        defaults.update(kw)
        return Appointment.objects.create(**defaults)


class AppointmentCreateTest(AppointmentBase):
    def test_create_defaults(self):
        appt = self.make_appointment()
        self.assertEqual(appt.salon, self.salon)
        self.assertEqual(appt.client, self.client)
        self.assertEqual(appt.employee, self.employee)
        self.assertEqual(appt.branch, self.branch)
        self.assertEqual(appt.status, Appointment.CREATED)
        self.assertEqual(appt.client_notes, "")
        self.assertEqual(appt.internal_notes, "")
        self.assertIsNone(appt.created_by)

    def test_create_with_all_fields(self):
        start = timezone.make_aware(datetime(2026, 9, 10, 10, 0))
        end = start + timedelta(hours=2)
        appt = self.make_appointment(
            status=Appointment.CONFIRMED,
            client_notes="note1",
            internal_notes="note2",
            created_by=self.user,
            start_datetime=start,
            end_datetime=end,
        )
        self.assertEqual(appt.status, Appointment.CONFIRMED)
        self.assertEqual(appt.client_notes, "note1")
        self.assertEqual(appt.internal_notes, "note2")
        self.assertEqual(appt.created_by, self.user)
        self.assertEqual(appt.start_datetime, start)
        self.assertEqual(appt.end_datetime, end)

    def test_id_is_uuid(self):
        appt = self.make_appointment()
        self.assertIsInstance(appt.id, uuid.UUID)
        self.assertTrue(Appointment._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(Appointment._meta.get_field("id").editable)

    def test_str(self):
        start = timezone.make_aware(datetime(2026, 9, 10, 10, 0))
        appt = self.make_appointment(start_datetime=start)
        self.assertEqual(str(appt), f"Alex — {start}")


class AppointmentStatusMetaTest(AppointmentBase):
    def test_status_constants(self):
        self.assertEqual(Appointment.CREATED, "CREATED")
        self.assertEqual(Appointment.CONFIRMED, "CONFIRMED")
        self.assertEqual(Appointment.IN_PROGRESS, "IN_PROGRESS")
        self.assertEqual(Appointment.COMPLETED, "COMPLETED")
        self.assertEqual(Appointment.CANCELLED, "CANCELLED")
        self.assertEqual(Appointment.NO_SHOW, "NO_SHOW")

    def test_status_choices(self):
        field = Appointment._meta.get_field("status")
        codes = {c[0] for c in field.choices}
        self.assertEqual(
            codes,
            {"CREATED", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"},
        )

    def test_status_max_length(self):
        self.assertEqual(Appointment._meta.get_field("status").max_length, 20)

    def test_status_default_created(self):
        self.assertEqual(Appointment._meta.get_field("status").default, "CREATED")


class AppointmentFieldMetaTest(AppointmentBase):
    def test_db_table(self):
        self.assertEqual(Appointment._meta.db_table, "appointments")

    def test_ordering(self):
        self.assertEqual(Appointment._meta.ordering, ["start_datetime"])

    def test_start_datetime(self):
        self.assertIsInstance(
            Appointment._meta.get_field("start_datetime"),
            __import__("django.db.models", fromlist=["DateTimeField"]).DateTimeField,
        )

    def test_end_datetime(self):
        self.assertIsInstance(
            Appointment._meta.get_field("end_datetime"),
            __import__("django.db.models", fromlist=["DateTimeField"]).DateTimeField,
        )

    def test_client_notes_blank(self):
        self.assertTrue(Appointment._meta.get_field("client_notes").blank)

    def test_internal_notes_blank(self):
        self.assertTrue(Appointment._meta.get_field("internal_notes").blank)

    def test_created_by_null_blank(self):
        field = Appointment._meta.get_field("created_by")
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_created_at_auto_now_add(self):
        self.assertTrue(Appointment._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(Appointment._meta.get_field("updated_at").auto_now)


class AppointmentRelationsTest(AppointmentBase):
    def test_salon_related_name(self):
        appt = self.make_appointment()
        self.assertIn(appt, self.salon.appointments.all())

    def test_client_protect(self):
        appt = self.make_appointment()
        with self.assertRaises(IntegrityError):
            self.client.delete()

    def test_employee_protect(self):
        appt = self.make_appointment()
        with self.assertRaises(IntegrityError):
            self.employee.delete()

    def test_branch_protect(self):
        appt = self.make_appointment()
        with self.assertRaises(IntegrityError):
            self.branch.delete()

    def test_client_related_name(self):
        appt = self.make_appointment()
        self.assertIn(appt, self.client.appointments.all())

    def test_employee_related_name(self):
        appt = self.make_appointment()
        self.assertIn(appt, self.employee.appointments.all())

    def test_branch_related_name(self):
        appt = self.make_appointment()
        self.assertIn(appt, self.branch.appointments.all())

    def test_created_by_set_null(self):
        appt = self.make_appointment(created_by=self.user)
        self.user.delete()
        appt.refresh_from_db()
        self.assertIsNone(appt.created_by)
        self.assertTrue(Appointment.objects.filter(id=appt.id).exists())

    def test_created_by_related_name(self):
        appt = self.make_appointment(created_by=self.user)
        self.assertIn(appt, self.user.created_appointments.all())

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            self.make_appointment(salon=None)


class AppointmentTimestampsTest(AppointmentBase):
    def test_created_at_set(self):
        appt = self.make_appointment()
        self.assertIsNotNone(appt.created_at)

    def test_updated_at_set(self):
        appt = self.make_appointment()
        self.assertIsNotNone(appt.updated_at)

    def test_created_at_unchanged_on_save(self):
        appt = self.make_appointment()
        old = appt.created_at
        appt.status = Appointment.COMPLETED
        appt.save()
        appt.refresh_from_db()
        self.assertEqual(appt.created_at, old)

    def test_updated_at_changes_on_save(self):
        appt = self.make_appointment()
        old = appt.updated_at
        appt.status = Appointment.COMPLETED
        appt.save()
        appt.refresh_from_db()
        self.assertGreaterEqual(appt.updated_at, old)


class AppointmentOrderingTest(AppointmentBase):
    def test_ordering_by_start_datetime(self):
        later = timezone.now() + timedelta(days=2)
        earlier = timezone.now() - timedelta(days=2)
        a1 = self.make_appointment(start_datetime=later)
        a2 = self.make_appointment(start_datetime=earlier)
        self.assertEqual(list(Appointment.objects.all()), [a2, a1])


class AppointmentServiceCreateTest(AppointmentBase):
    def setUp(self):
        super().setUp()
        self.appointment = self.make_appointment()

    def test_create(self):
        asvc = AppointmentService.objects.create(
            appointment=self.appointment,
            service=self.service,
            price=Decimal("150.00"),
            duration_minutes=45,
        )
        self.assertEqual(asvc.appointment, self.appointment)
        self.assertEqual(asvc.service, self.service)
        self.assertEqual(asvc.price, Decimal("150.00"))
        self.assertEqual(asvc.duration_minutes, 45)

    def test_id_is_uuid(self):
        asvc = AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertIsInstance(asvc.id, uuid.UUID)
        self.assertTrue(AppointmentService._meta.get_field("id").primary_key)

    def test_db_table(self):
        self.assertEqual(AppointmentService._meta.db_table, "appointment_services")

    def test_str(self):
        start = timezone.make_aware(datetime(2026, 9, 10, 10, 0))
        appt = self.make_appointment(start_datetime=start)
        asvc = AppointmentService.objects.create(
            appointment=appt, service=self.service,
            price=Decimal("100"), duration_minutes=30,
        )
        self.assertEqual(str(asvc), f"Alex — {start} — S")

    def test_price_decimal(self):
        asvc = AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("99.99"), duration_minutes=20,
        )
        self.assertEqual(asvc.price, Decimal("99.99"))
        self.assertIsInstance(asvc.price, Decimal)


class AppointmentServiceFieldMetaTest(AppointmentBase):
    def test_price_decimal(self):
        field = AppointmentService._meta.get_field("price")
        self.assertEqual(field.max_digits, 10)
        self.assertEqual(field.decimal_places, 2)

    def test_duration_positive_integer(self):
        field = AppointmentService._meta.get_field("duration_minutes")
        self.assertIsInstance(
            field,
            __import__("django.db.models", fromlist=["PositiveIntegerField"]).PositiveIntegerField,
        )

    def test_created_at_auto_now_add(self):
        self.assertTrue(AppointmentService._meta.get_field("created_at").auto_now_add)


class AppointmentServiceRelationsTest(AppointmentBase):
    def setUp(self):
        super().setUp()
        self.appointment = self.make_appointment()

    def test_appointment_cascade(self):
        asvc = AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("1"), duration_minutes=10,
        )
        self.appointment.delete()
        self.assertFalse(AppointmentService.objects.filter(id=asvc.id).exists())

    def test_appointment_related_name(self):
        asvc = AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertIn(asvc, self.appointment.appointment_services.all())

    def test_service_protect(self):
        AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("1"), duration_minutes=10,
        )
        with self.assertRaises(IntegrityError):
            self.service.delete()

    def test_service_related_name(self):
        asvc = AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertIn(asvc, self.service.appointment_services.all())

    def test_appointment_required(self):
        with self.assertRaises(IntegrityError):
            AppointmentService.objects.create(
                appointment=None, service=self.service,
                price=Decimal("1"), duration_minutes=10,
            )

    def test_many_services_per_appointment(self):
        category2 = ServiceCategory.objects.create(salon=self.salon, name="C2")
        service2 = Service.objects.create(
            salon=self.salon, category=category2, name="S2",
            price=Decimal("200"), duration_minutes=60,
        )
        AppointmentService.objects.create(
            appointment=self.appointment, service=self.service,
            price=Decimal("1"), duration_minutes=10,
        )
        AppointmentService.objects.create(
            appointment=self.appointment, service=service2,
            price=Decimal("2"), duration_minutes=20,
        )
        self.assertEqual(self.appointment.appointment_services.count(), 2)


class AppointmentStatusHistoryCreateTest(AppointmentBase):
    def setUp(self):
        super().setUp()
        self.appointment = self.make_appointment()

    def test_create(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment,
            status=Appointment.CONFIRMED,
            changed_by=self.user,
            comment="over phone",
        )
        self.assertEqual(hist.appointment, self.appointment)
        self.assertEqual(hist.status, Appointment.CONFIRMED)
        self.assertEqual(hist.changed_by, self.user)
        self.assertEqual(hist.comment, "over phone")

    def test_create_minimal(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment,
            status=Appointment.CREATED,
        )
        self.assertEqual(hist.comment, "")
        self.assertIsNone(hist.changed_by)

    def test_id_is_uuid(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CREATED,
        )
        self.assertIsInstance(hist.id, uuid.UUID)
        self.assertTrue(AppointmentStatusHistory._meta.get_field("id").primary_key)

    def test_db_table(self):
        self.assertEqual(AppointmentStatusHistory._meta.db_table, "appointment_status_history")

    def test_ordering(self):
        self.assertEqual(AppointmentStatusHistory._meta.ordering, ["created_at"])

    def test_str(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CONFIRMED,
        )
        start = self.appointment.start_datetime
        self.assertEqual(str(hist), f"Alex — {start} — CONFIRMED")

    def test_status_choices(self):
        field = AppointmentStatusHistory._meta.get_field("status")
        codes = {c[0] for c in field.choices}
        self.assertEqual(
            codes,
            {"CREATED", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"},
        )

    def test_status_max_length(self):
        self.assertEqual(AppointmentStatusHistory._meta.get_field("status").max_length, 20)

    def test_comment_blank(self):
        self.assertTrue(AppointmentStatusHistory._meta.get_field("comment").blank)

    def test_created_at_auto_now_add(self):
        self.assertTrue(AppointmentStatusHistory._meta.get_field("created_at").auto_now_add)


class AppointmentStatusHistoryRelationsTest(AppointmentBase):
    def setUp(self):
        super().setUp()
        self.appointment = self.make_appointment()

    def test_appointment_cascade(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CREATED,
        )
        self.appointment.delete()
        self.assertFalse(AppointmentStatusHistory.objects.filter(id=hist.id).exists())

    def test_appointment_related_name(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CREATED,
        )
        self.assertIn(hist, self.appointment.status_history.all())

    def test_changed_by_set_null(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CREATED,
            changed_by=self.user,
        )
        self.user.delete()
        hist.refresh_from_db()
        self.assertIsNone(hist.changed_by)
        self.assertTrue(AppointmentStatusHistory.objects.filter(id=hist.id).exists())

    def test_changed_by_related_name(self):
        hist = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CREATED,
            changed_by=self.user,
        )
        self.assertIn(hist, self.user.appointment_status_changes.all())

    def test_appointment_required(self):
        with self.assertRaises(IntegrityError):
            AppointmentStatusHistory.objects.create(appointment=None, status=Appointment.CREATED)

    def test_ordering_by_created_at(self):
        h1 = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CREATED,
        )
        h2 = AppointmentStatusHistory.objects.create(
            appointment=self.appointment, status=Appointment.CONFIRMED,
        )
        self.assertEqual(list(AppointmentStatusHistory.objects.all()), [h1, h2])
