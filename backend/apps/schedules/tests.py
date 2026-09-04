import uuid
from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.tenants.models import Salon
from apps.employee.models import Employee
from apps.branch.models import Branch
from apps.schedules.models import Schedule, ScheduleBreak


# ===========================================================================
# Schedule – Creation & Basic Properties
# ===========================================================================


class ScheduleCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")

    def _make(self, **kw):
        defaults = dict(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=Schedule.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        defaults.update(kw)
        return Schedule.objects.create(**defaults)

    def test_create_valid(self):
        s = self._make()
        self.assertEqual(s.employee, self.employee)
        self.assertEqual(s.branch, self.branch)
        self.assertEqual(s.salon, self.salon)
        self.assertEqual(s.weekday, Schedule.MONDAY)
        self.assertEqual(s.start_time, time(9, 0))
        self.assertEqual(s.end_time, time(18, 0))
        self.assertTrue(s.is_active)

    def test_create_all_weekdays(self):
        for day in range(7):
            s = self._make(weekday=day)
            self.assertEqual(s.weekday, day)

    def test_id_is_uuid(self):
        s = self._make()
        self.assertIsInstance(s.id, uuid.UUID)

    def test_id_is_primary_key(self):
        self.assertTrue(Schedule._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(Schedule._meta.get_field("id").editable)

    def test_is_active_default_true(self):
        s = self._make()
        self.assertTrue(s.is_active)

    def test_is_active_can_be_false(self):
        s = self._make(is_active=False)
        self.assertFalse(s.is_active)

    def test_unique_ids(self):
        s1 = self._make(weekday=0)
        s2 = self._make(weekday=1)
        self.assertNotEqual(s1.id, s2.id)


# ===========================================================================
# Schedule – __str__
# ===========================================================================


class ScheduleStrTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")

    def _make(self, **kw):
        defaults = dict(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=Schedule.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        defaults.update(kw)
        return Schedule.objects.create(**defaults)

    def test_str_monday(self):
        s = self._make(weekday=Schedule.MONDAY)
        # Employee.__str__ = "Ivan", Branch.__str__ = "Hub — Downtown"
        self.assertEqual(str(s), "Ivan — Hub — Downtown — Monday")

    def test_str_sunday(self):
        s = self._make(weekday=Schedule.SUNDAY)
        self.assertEqual(str(s), "Ivan — Hub — Downtown — Sunday")

    def test_str_contains_get_weekday_display(self):
        for val, label in Schedule.WEEKDAY_CHOICES:
            s = self._make(weekday=val)
            self.assertIn(label, str(s))

    def test_str_with_employee_last_name(self):
        emp = Employee.objects.create(
            salon=self.salon, first_name="Ivan", last_name="Petrov"
        )
        b = Branch.objects.create(salon=self.salon, name="Center")
        s = self._make(employee=emp, branch=b, weekday=Schedule.WEDNESDAY)
        self.assertEqual(str(s), "Ivan Petrov — Hub — Center — Wednesday")

    def test_str_parts_separated_by_dash(self):
        s = self._make()
        parts = str(s).split(" — ")
        self.assertEqual(len(parts), 4)


# ===========================================================================
# Schedule – Field Types & Meta
# ===========================================================================


class ScheduleFieldMetaTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")

    def test_db_table(self):
        self.assertEqual(Schedule._meta.db_table, "schedules")

    def test_weekday_field_type(self):
        from django.db.models import PositiveSmallIntegerField

        field = Schedule._meta.get_field("weekday")
        self.assertIsInstance(field, PositiveSmallIntegerField)

    def test_weekday_choices_count(self):
        field = Schedule._meta.get_field("weekday")
        self.assertEqual(len(field.choices), 7)

    def test_weekday_choices_are_tuples(self):
        for choice in Schedule.WEEKDAY_CHOICES:
            self.assertIsInstance(choice, tuple)
            self.assertEqual(len(choice), 2)

    def test_weekday_constants(self):
        self.assertEqual(Schedule.MONDAY, 0)
        self.assertEqual(Schedule.TUESDAY, 1)
        self.assertEqual(Schedule.WEDNESDAY, 2)
        self.assertEqual(Schedule.THURSDAY, 3)
        self.assertEqual(Schedule.FRIDAY, 4)
        self.assertEqual(Schedule.SATURDAY, 5)
        self.assertEqual(Schedule.SUNDAY, 6)

    def test_get_weekday_display_all(self):
        expected = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        }
        for val, label in expected.items():
            s = Schedule.objects.create(
                salon=self.salon,
                employee=self.employee,
                branch=self.branch,
                weekday=val,
                start_time=time(9, 0),
                end_time=time(18, 0),
            )
            self.assertEqual(s.get_weekday_display(), label)

    def test_start_time_is_time_field(self):
        from django.db.models import TimeField

        self.assertIsInstance(Schedule._meta.get_field("start_time"), TimeField)

    def test_end_time_is_time_field(self):
        from django.db.models import TimeField

        self.assertIsInstance(Schedule._meta.get_field("end_time"), TimeField)

    def test_is_active_default_true(self):
        self.assertTrue(Schedule._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        self.assertTrue(Schedule._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(Schedule._meta.get_field("updated_at").auto_now)

    def test_constraint_name(self):
        names = {c.name for c in Schedule._meta.constraints}
        self.assertIn("unique_employee_branch_weekday_schedule", names)

    def test_constraint_type(self):
        from django.db.models import UniqueConstraint

        for c in Schedule._meta.constraints:
            if c.name == "unique_employee_branch_weekday_schedule":
                self.assertIsInstance(c, UniqueConstraint)
                break

    def test_constraint_fields(self):
        for c in Schedule._meta.constraints:
            if c.name == "unique_employee_branch_weekday_schedule":
                self.assertEqual(
                    set(c.fields), {"employee", "branch", "weekday"}
                )
                break

    def test_salon_fk_cascade(self):
        field = Schedule._meta.get_field("salon")
        self.assertEqual(field.remote_field.on_delete.__name__, "CASCADE")

    def test_employee_fk_cascade(self):
        field = Schedule._meta.get_field("employee")
        self.assertEqual(field.remote_field.on_delete.__name__, "CASCADE")

    def test_branch_fk_cascade(self):
        field = Schedule._meta.get_field("branch")
        self.assertEqual(field.remote_field.on_delete.__name__, "CASCADE")


# ===========================================================================
# Schedule – Relations
# ===========================================================================


class ScheduleRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")

    def _make(self, **kw):
        defaults = dict(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        defaults.update(kw)
        return Schedule.objects.create(**defaults)

    def test_employee_required(self):
        with self.assertRaises(ValidationError) as ctx:
            Schedule.objects.create(
                salon=self.salon,
                employee=None,
                branch=self.branch,
                weekday=0,
                start_time=time(9, 0),
                end_time=time(18, 0),
            )
        self.assertIn("employee", ctx.exception.message_dict)

    def test_branch_required(self):
        with self.assertRaises(ValidationError) as ctx:
            Schedule.objects.create(
                salon=self.salon,
                employee=self.employee,
                branch=None,
                weekday=0,
                start_time=time(9, 0),
                end_time=time(18, 0),
            )
        self.assertIn("branch", ctx.exception.message_dict)

    def test_salon_required(self):
        with self.assertRaises(ValidationError) as ctx:
            Schedule.objects.create(
                salon=None,
                employee=self.employee,
                branch=self.branch,
                weekday=0,
                start_time=time(9, 0),
                end_time=time(18, 0),
            )
        self.assertIn("salon", ctx.exception.message_dict)

    def test_employee_related_name(self):
        s = self._make()
        self.assertIn(s, self.employee.employee_schedules.all())

    def test_branch_related_name(self):
        s = self._make()
        self.assertIn(s, self.branch.branch_schedules.all())

    def test_salon_related_name(self):
        s = self._make()
        self.assertIn(s, self.salon.salon_schedules.all())

    def test_cascade_delete_employee(self):
        s = self._make()
        self.employee.delete()
        self.assertFalse(Schedule.objects.filter(id=s.id).exists())

    def test_cascade_delete_branch(self):
        s = self._make()
        self.branch.delete()
        self.assertFalse(Schedule.objects.filter(id=s.id).exists())

    def test_cascade_delete_salon(self):
        s = self._make()
        self.salon.delete()
        self.assertFalse(Schedule.objects.filter(id=s.id).exists())

    def test_multiple_schedules_per_employee(self):
        self._make(weekday=0)
        self._make(weekday=1)
        self.assertEqual(self.employee.employee_schedules.count(), 2)

    def test_multiple_schedules_per_branch(self):
        self._make(weekday=0)
        self._make(weekday=1)
        self.assertEqual(self.branch.branch_schedules.count(), 2)

    def test_schedule_accesses_related_salon(self):
        s = self._make()
        self.assertEqual(s.salon.name, "Hub")

    def test_schedule_accesses_related_employee(self):
        s = self._make()
        self.assertEqual(s.employee.first_name, "Ivan")

    def test_schedule_accesses_related_branch(self):
        s = self._make()
        self.assertEqual(s.branch.name, "B")


# ===========================================================================
# Schedule – Unique Constraint
# ===========================================================================


class ScheduleUniqueConstraintTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.employee2 = Employee.objects.create(salon=self.salon, first_name="Petr")
        self.branch = Branch.objects.create(salon=self.salon, name="B1")
        self.branch2 = Branch.objects.create(salon=self.salon, name="B2")

    def _make(self, employee=None, branch=None, weekday=0):
        return Schedule.objects.create(
            salon=self.salon,
            employee=employee or self.employee,
            branch=branch or self.branch,
            weekday=weekday,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def test_same_triple_raises(self):
        self._make(weekday=0)
        with self.assertRaises(ValidationError) as ctx:
            self._make(weekday=0)
        self.assertIn("__all__", ctx.exception.message_dict)

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

    def test_unique_constraint_error_message(self):
        self._make(weekday=0)
        with self.assertRaises(ValidationError) as ctx:
            self._make(weekday=0)
        msg = ctx.exception.message_dict["__all__"][0]
        self.assertIn("already exists", msg.lower())

    def test_same_triple_different_salon_ok(self):
        salon2 = Salon.objects.create(name="Hub2", slug="hub2")
        emp2 = Employee.objects.create(salon=salon2, first_name="Ivan")
        br2 = Branch.objects.create(salon=salon2, name="B1")
        self._make(weekday=0)
        s2 = Schedule.objects.create(
            salon=salon2,
            employee=emp2,
            branch=br2,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        self.assertIsNotNone(s2.id)


# ===========================================================================
# Schedule – clean() Validation
# ===========================================================================


class ScheduleCleanValidationTest(TestCase):
    def setUp(self):
        self.salon_a = Salon.objects.create(name="Salon A", slug="salon-a")
        self.salon_b = Salon.objects.create(name="Salon B", slug="salon-b")
        self.employee_a = Employee.objects.create(
            salon=self.salon_a, first_name="Ivan"
        )
        self.employee_b = Employee.objects.create(
            salon=self.salon_b, first_name="Petr"
        )
        self.branch_a = Branch.objects.create(salon=self.salon_a, name="Branch A")
        self.branch_b = Branch.objects.create(salon=self.salon_b, name="Branch B")

    def _sched(self, **kw):
        defaults = dict(
            salon=self.salon_a,
            employee=self.employee_a,
            branch=self.branch_a,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        defaults.update(kw)
        return Schedule(**defaults)

    def test_employee_from_different_salon(self):
        s = self._sched(employee=self.employee_b)
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("employee", ctx.exception.message_dict)
        self.assertIn(
            "different salon", ctx.exception.message_dict["employee"][0].lower()
        )

    def test_branch_from_different_salon(self):
        s = self._sched(branch=self.branch_b)
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("branch", ctx.exception.message_dict)
        self.assertIn(
            "different salon", ctx.exception.message_dict["branch"][0].lower()
        )

    def test_both_wrong_first_error_is_employee(self):
        s = self._sched(employee=self.employee_b, branch=self.branch_b)
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("employee", ctx.exception.message_dict)

    def test_cross_check_employee_branch_different_salons(self):
        s = self._sched(salon=None, employee=self.employee_a, branch=self.branch_b)
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("branch", ctx.exception.message_dict)
        self.assertIn("salon", ctx.exception.message_dict)

    def test_end_time_before_start_time(self):
        s = self._sched(start_time=time(18, 0), end_time=time(9, 0))
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("end_time", ctx.exception.message_dict)
        self.assertIn(
            "after start time", ctx.exception.message_dict["end_time"][0].lower()
        )

    def test_end_time_equals_start_time(self):
        s = self._sched(start_time=time(12, 0), end_time=time(12, 0))
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        self.assertIn("end_time", ctx.exception.message_dict)

    def test_same_salon_passes_clean(self):
        s = self._sched()
        s.full_clean()

    def test_save_calls_full_clean_employee_mismatch(self):
        with self.assertRaises(ValidationError):
            Schedule.objects.create(
                salon=self.salon_a,
                employee=self.employee_b,
                branch=self.branch_a,
                weekday=0,
                start_time=time(9, 0),
                end_time=time(18, 0),
            )

    def test_save_calls_full_clean_time_invalid(self):
        with self.assertRaises(ValidationError):
            Schedule.objects.create(
                salon=self.salon_a,
                employee=self.employee_a,
                branch=self.branch_a,
                weekday=0,
                start_time=time(18, 0),
                end_time=time(9, 0),
            )

    def test_clean_directly_vs_full_clean(self):
        s = self._sched(employee=self.employee_b, start_time=time(18, 0), end_time=time(9, 0))
        with self.assertRaises(ValidationError):
            s.clean()

    def test_valid_times_pass_clean(self):
        s = self._sched(start_time=time(8, 0), end_time=time(17, 0))
        s.full_clean()

    def test_boundary_start_before_end(self):
        s = self._sched(start_time=time(9, 0), end_time=time(9, 0, 1))
        s.full_clean()

    def test_multiple_errors_at_once(self):
        s = self._sched(salon=None, employee=self.employee_a, branch=self.branch_b)
        with self.assertRaises(ValidationError) as ctx:
            s.full_clean()
        errors = ctx.exception.message_dict
        self.assertTrue(len(errors) >= 2)


# ===========================================================================
# Schedule – Timestamps
# ===========================================================================


class ScheduleTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.sched = Schedule.objects.create(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
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


# ===========================================================================
# ScheduleBreak – Creation & Basic Properties
# ===========================================================================


class ScheduleBreakCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def test_create_valid(self):
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
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        self.assertIsInstance(brk.id, uuid.UUID)

    def test_id_is_primary_key(self):
        self.assertTrue(ScheduleBreak._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(ScheduleBreak._meta.get_field("id").editable)

    def test_unique_ids(self):
        b1 = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(12, 0), end_time=time(13, 0)
        )
        b2 = ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(15, 0), end_time=time(16, 0)
        )
        self.assertNotEqual(b1.id, b2.id)


# ===========================================================================
# ScheduleBreak – __str__
# ===========================================================================


class ScheduleBreakStrTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=Schedule.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def test_str(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        # Schedule.__str__ = "Ivan — Hub — B — Monday"
        self.assertEqual(
            str(brk),
            "Ivan — Hub — B — Monday — 13:00:00 - 14:00:00",
        )

    def test_str_contains_schedule_str(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        self.assertIn(str(self.schedule), str(brk))

    def test_str_contains_times(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 30),
            end_time=time(14, 30),
        )
        s = str(brk)
        self.assertIn("13:30:00", s)
        self.assertIn("14:30:00", s)


# ===========================================================================
# ScheduleBreak – Field Types & Meta
# ===========================================================================


class ScheduleBreakFieldMetaTest(TestCase):
    def test_db_table(self):
        self.assertEqual(ScheduleBreak._meta.db_table, "schedule_breaks")

    def test_start_time_is_time_field(self):
        from django.db.models import TimeField

        self.assertIsInstance(
            ScheduleBreak._meta.get_field("start_time"), TimeField
        )

    def test_end_time_is_time_field(self):
        from django.db.models import TimeField

        self.assertIsInstance(
            ScheduleBreak._meta.get_field("end_time"), TimeField
        )

    def test_created_at_auto_now_add(self):
        self.assertTrue(
            ScheduleBreak._meta.get_field("created_at").auto_now_add
        )

    def test_updated_at_auto_now(self):
        self.assertTrue(ScheduleBreak._meta.get_field("updated_at").auto_now)

    def test_schedule_fk_cascade(self):
        field = ScheduleBreak._meta.get_field("schedule")
        self.assertEqual(field.remote_field.on_delete.__name__, "CASCADE")


# ===========================================================================
# ScheduleBreak – Relations
# ===========================================================================


class ScheduleBreakRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def test_schedule_required(self):
        with self.assertRaises(ValidationError) as ctx:
            ScheduleBreak.objects.create(
                schedule=None,
                start_time=time(13, 0),
                end_time=time(14, 0),
            )
        self.assertIn("schedule", ctx.exception.message_dict)

    def test_related_name_breaks(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        self.assertIn(brk, self.schedule.breaks.all())

    def test_cascade_delete_schedule(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        self.schedule.delete()
        self.assertFalse(ScheduleBreak.objects.filter(id=brk.id).exists())

    def test_multiple_breaks_per_schedule(self):
        ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(12, 0), end_time=time(13, 0)
        )
        ScheduleBreak.objects.create(
            schedule=self.schedule, start_time=time(15, 0), end_time=time(16, 0)
        )
        self.assertEqual(self.schedule.breaks.count(), 2)

    def test_break_count_zero(self):
        self.assertEqual(self.schedule.breaks.count(), 0)

    def test_break_accesses_schedule(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        self.assertEqual(brk.schedule.employee, self.employee)


# ===========================================================================
# ScheduleBreak – clean() Validation
# ===========================================================================


class ScheduleBreakCleanValidationTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

    def _brk(self, **kw):
        defaults = dict(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        defaults.update(kw)
        return ScheduleBreak(**defaults)

    def test_end_time_before_start_time(self):
        brk = self._brk(start_time=time(14, 0), end_time=time(13, 0))
        with self.assertRaises(ValidationError) as ctx:
            brk.full_clean()
        self.assertIn("end_time", ctx.exception.message_dict)
        self.assertIn(
            "Break end time must be after start time.",
            ctx.exception.message_dict["end_time"],
        )

    def test_end_time_equals_start_time(self):
        brk = self._brk(start_time=time(13, 0), end_time=time(13, 0))
        with self.assertRaises(ValidationError) as ctx:
            brk.full_clean()
        self.assertIn("end_time", ctx.exception.message_dict)

    def test_valid_break_passes_clean(self):
        brk = self._brk(start_time=time(13, 0), end_time=time(14, 0))
        brk.full_clean()

    def test_save_calls_full_clean_invalid_times(self):
        with self.assertRaises(ValidationError):
            ScheduleBreak.objects.create(
                schedule=self.schedule,
                start_time=time(14, 0),
                end_time=time(13, 0),
            )

    def test_save_calls_full_clean_valid(self):
        brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        self.assertIsNotNone(brk.id)

    def test_clean_directly(self):
        brk = self._brk(start_time=time(14, 0), end_time=time(13, 0))
        with self.assertRaises(ValidationError):
            brk.clean()

    def test_boundary_one_second_after(self):
        brk = self._brk(start_time=time(13, 0), end_time=time(13, 0, 1))
        brk.full_clean()

    def test_break_within_schedule_time(self):
        brk = self._brk(start_time=time(9, 0), end_time=time(18, 0))
        brk.full_clean()

    def test_break_at_schedule_boundaries(self):
        brk = self._brk(start_time=time(9, 0), end_time=time(18, 0))
        brk.full_clean()


# ===========================================================================
# ScheduleBreak – Timestamps
# ===========================================================================


class ScheduleBreakTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.schedule = Schedule.objects.create(
            salon=self.salon,
            employee=self.employee,
            branch=self.branch,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        )
        self.brk = ScheduleBreak.objects.create(
            schedule=self.schedule,
            start_time=time(13, 0),
            end_time=time(14, 0),
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
