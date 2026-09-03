import uuid
from datetime import time

from django.db import IntegrityError
from django.test import TestCase

from apps.tenants.models import Salon
from apps.employee.models import Employee
from apps.branch.models import Branch
from apps.schedules.models import Schedule, ScheduleBreak


class ScheduleCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")

    def test_create(self):
        sched = Schedule.objects.create(
            employee=self.employee,
            branch=self.branch,
            weekday=Schedule.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        self.assertEqual(sched.employee, self.employee)
        self.assertEqual(sched.branch, self.branch)
        self.assertEqual(sched.weekday, Schedule.MONDAY)
        self.assertEqual(sched.start_time, time(9, 0))
        self.assertEqual(sched.end_time, time(18, 0))
        self.assertTrue(sched.is_active)

    def test_id_is_uuid(self):
        sched = Schedule.objects.create(
            employee=self.employee, branch=self.branch,
            weekday=0, start_time=time(9, 0), end_time=time(18, 0),
        )
        self.assertIsInstance(sched.id, uuid.UUID)
        self.assertTrue(Schedule._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(Schedule._meta.get_field("id").editable)

    def test_str(self):
        sched = Schedule.objects.create(
            employee=self.employee, branch=self.branch,
            weekday=Schedule.MONDAY, start_time=time(9, 0), end_time=time(18, 0),
        )
        self.assertEqual(str(sched), "Ivan — Hub — Downtown — Monday")


class ScheduleFieldMetaTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")

    def _make(self, **kw):
        defaults = dict(
            employee=self.employee, branch=self.branch,
            weekday=0, start_time=time(9, 0), end_time=time(18, 0),
        )
        defaults.update(kw)
        return Schedule.objects.create(**defaults)

    def test_db_table(self):
        self.assertEqual(Schedule._meta.db_table, "schedules")

    def test_weekday_positive_small_integer(self):
        field = Schedule._meta.get_field("weekday")
        self.assertIsInstance(
            field,
            __import__("django.db.models", fromlist=["PositiveSmallIntegerField"]).PositiveSmallIntegerField,
        )

    def test_weekday_choices(self):
        field = Schedule._meta.get_field("weekday")
        self.assertEqual(len(field.choices), 7)

    def test_weekday_constants(self):
        self.assertEqual(Schedule.MONDAY, 0)
        self.assertEqual(Schedule.TUESDAY, 1)
        self.assertEqual(Schedule.WEDNESDAY, 2)
        self.assertEqual(Schedule.THURSDAY, 3)
        self.assertEqual(Schedule.FRIDAY, 4)
        self.assertEqual(Schedule.SATURDAY, 5)
        self.assertEqual(Schedule.SUNDAY, 6)

    def test_get_weekday_display(self):
        sched = self._make(weekday=Schedule.FRIDAY)
        self.assertEqual(sched.get_weekday_display(), "Friday")

    def test_get_weekday_display_all(self):
        expected = {
            0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
            4: "Friday", 5: "Saturday", 6: "Sunday",
        }
        for val, label in expected.items():
            sched = self._make(weekday=val)
            self.assertEqual(sched.get_weekday_display(), label)

    def test_start_time_is_time_field(self):
        self.assertIsInstance(
            Schedule._meta.get_field("start_time"),
            __import__("django.db.models", fromlist=["TimeField"]).TimeField,
        )

    def test_end_time_is_time_field(self):
        self.assertIsInstance(
            Schedule._meta.get_field("end_time"),
            __import__("django.db.models", fromlist=["TimeField"]).TimeField,
        )

    def test_is_active_default_true(self):
        self.assertTrue(Schedule._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        self.assertTrue(Schedule._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(Schedule._meta.get_field("updated_at").auto_now)


class ScheduleRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")

    def _make(self, employee=None, branch=None, weekday=0):
        return Schedule.objects.create(
            employee=employee or self.employee,
            branch=branch or self.branch,
            weekday=weekday,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def test_employee_required(self):
        with self.assertRaises(IntegrityError):
            Schedule.objects.create(
                employee=None, branch=self.branch,
                weekday=0, start_time=time(9, 0), end_time=time(18, 0),
            )

    def test_branch_required(self):
        with self.assertRaises(IntegrityError):
            Schedule.objects.create(
                employee=self.employee, branch=None,
                weekday=0, start_time=time(9, 0), end_time=time(18, 0),
            )

    def test_employee_related_name(self):
        sched = self._make()
        self.assertIn(sched, self.employee.schedules.all())

    def test_branch_related_name(self):
        sched = self._make()
        self.assertIn(sched, self.branch.schedules.all())

    def test_employee_cascade(self):
        sched = self._make()
        self.employee.delete()
        self.assertFalse(Schedule.objects.filter(id=sched.id).exists())

    def test_branch_cascade(self):
        sched = self._make()
        self.branch.delete()
        self.assertFalse(Schedule.objects.filter(id=sched.id).exists())

    def test_multiple_schedules_per_employee(self):
        self._make(weekday=0)
        self._make(weekday=1)
        self.assertEqual(self.employee.schedules.count(), 2)


class ScheduleUniqueConstraintTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.employee2 = Employee.objects.create(salon=self.salon, first_name="Petr")
        self.branch = Branch.objects.create(salon=self.salon, name="B1")
        self.branch2 = Branch.objects.create(salon=self.salon, name="B2")

    def _make(self, employee=None, branch=None, weekday=0):
        return Schedule.objects.create(
            employee=employee or self.employee,
            branch=branch or self.branch,
            weekday=weekday,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def test_same_triple_raises(self):
        self._make(weekday=0)
        with self.assertRaises(IntegrityError):
            self._make(weekday=0)

    def test_different_weekday_ok(self):
        self._make(weekday=0)
        s2 = self._make(weekday=1)
        self.assertIsNotNone(s2.id)

    def test_different_branch_ok(self):
        self._make(weekday=0)
        s2 = self._make(branch=self.branch2, weekday=0)
        self.assertIsNotNone(s2.id)

    def test_different_employee_ok(self):
        self._make(weekday=0)
        s2 = self._make(employee=self.employee2, weekday=0)
        self.assertIsNotNone(s2.id)

    def test_constraint_name(self):
        names = {c.name for c in Schedule._meta.constraints}
        self.assertIn("unique_employee_branch_weekday_schedule", names)


class ScheduleTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.sched = Schedule.objects.create(
            employee=self.employee, branch=self.branch,
            weekday=0, start_time=time(9, 0), end_time=time(18, 0),
        )

    def test_created_at_set(self):
        self.assertIsNotNone(self.sched.created_at)

    def test_updated_at_set(self):
        self.assertIsNotNone(self.sched.updated_at)

    def test_created_at_unchanged_on_save(self):
        old = self.sched.created_at
        self.sched.end_time = time(20, 0)
        self.sched.save()
        self.sched.refresh_from_db()
        self.assertEqual(self.sched.created_at, old)

    def test_updated_at_changes_on_save(self):
        old = self.sched.updated_at
        self.sched.end_time = time(20, 0)
        self.sched.save()
        self.sched.refresh_from_db()
        self.assertGreaterEqual(self.sched.updated_at, old)


class ScheduleBreakCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            employee=self.employee, branch=self.branch,
            weekday=0, start_time=time(9, 0), end_time=time(18, 0),
        )

    def test_create(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        self.assertEqual(brk.schedule, self.schedule)
        self.assertEqual(brk.start_time, time(13, 0))
        self.assertEqual(brk.end_time, time(14, 0))

    def test_id_is_uuid(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(13, 0), end_time=time(14, 0),
        )
        self.assertIsInstance(brk.id, uuid.UUID)
        self.assertTrue(ScheduleBreak._meta.get_field("id").primary_key)

    def test_db_table(self):
        self.assertEqual(ScheduleBreak._meta.db_table, "schedule_breaks")

    def test_str(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(13, 0), end_time=time(14, 0),
        )
        self.assertEqual(
            str(brk),
            "Ivan — Hub — B — Monday — 13:00:00 - 14:00:00",
        )


class ScheduleBreakFieldMetaTest(TestCase):
    def test_start_time_time_field(self):
        self.assertIsInstance(
            ScheduleBreak._meta.get_field("start_time"),
            __import__("django.db.models", fromlist=["TimeField"]).TimeField,
        )

    def test_end_time_time_field(self):
        self.assertIsInstance(
            ScheduleBreak._meta.get_field("end_time"),
            __import__("django.db.models", fromlist=["TimeField"]).TimeField,
        )

    def test_created_at_auto_now_add(self):
        self.assertTrue(ScheduleBreak._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(ScheduleBreak._meta.get_field("updated_at").auto_now)


class ScheduleBreakRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            employee=self.employee, branch=self.branch,
            weekday=0, start_time=time(9, 0), end_time=time(18, 0),
        )

    def test_schedule_required(self):
        with self.assertRaises(IntegrityError):
            ScheduleBreak.objects.create(
                schedule=None, start_time=time(13, 0), end_time=time(14, 0),
            )

    def test_related_name(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(13, 0), end_time=time(14, 0),
        )
        self.assertIn(brk, self.schedule.breaks.all())

    def test_cascade_delete_schedule(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(13, 0), end_time=time(14, 0),
        )
        self.schedule.delete()
        self.assertFalse(ScheduleBreak.objects.filter(id=brk.id).exists())

    def test_multiple_breaks_per_schedule(self):
        ScheduleBreak.objects.create(schedule=self.schedule, start_time=time(12, 0), end_time=time(13, 0))
        ScheduleBreak.objects.create(schedule=self.schedule, start_time=time(15, 0), end_time=time(16, 0))
        self.assertEqual(self.schedule.breaks.count(), 2)


class ScheduleBreakTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            employee=self.employee, branch=self.branch,
            weekday=0, start_time=time(9, 0), end_time=time(18, 0),
        )
        self.brk = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(13, 0), end_time=time(14, 0),
        )

    def test_created_at_set(self):
        self.assertIsNotNone(self.brk.created_at)

    def test_updated_at_set(self):
        self.assertIsNotNone(self.brk.updated_at)

    def test_created_at_unchanged_on_save(self):
        old = self.brk.created_at
        self.brk.end_time = time(15, 0)
        self.brk.save()
        self.brk.refresh_from_db()
        self.assertEqual(self.brk.created_at, old)

    def test_updated_at_changes_on_save(self):
        old = self.brk.updated_at
        self.brk.end_time = time(15, 0)
        self.brk.save()
        self.brk.refresh_from_db()
        self.assertGreaterEqual(self.brk.updated_at, old)
