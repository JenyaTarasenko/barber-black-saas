import uuid

from django.db import IntegrityError
from django.test import TestCase

from apps.tenants.models import Salon
from apps.employee.models import Employee, EmployeeBranch
from apps.branch.models import Branch


class EmployeeCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Barber Hub", slug="barber-hub")

    def test_create_employee(self):
        emp = Employee.objects.create(
            salon=self.salon,
            first_name="Ivan",
            last_name="Petrov",
            phone="+79991112233",
            email="ivan@test.com",
        )
        self.assertEqual(emp.salon, self.salon)
        self.assertEqual(emp.first_name, "Ivan")
        self.assertEqual(emp.last_name, "Petrov")
        self.assertEqual(emp.phone, "+79991112233")
        self.assertEqual(emp.email, "ivan@test.com")

    def test_create_employee_minimal(self):
        emp = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.assertEqual(emp.last_name, "")
        self.assertEqual(emp.phone, "")
        self.assertEqual(emp.email, "")
        self.assertTrue(emp.is_active)

    def test_id_is_uuid(self):
        emp = Employee.objects.create(salon=self.salon, first_name="A")
        self.assertIsInstance(emp.id, uuid.UUID)

    def test_id_primary_key(self):
        field = Employee._meta.get_field("id")
        self.assertTrue(field.primary_key)
        self.assertFalse(field.editable)

    def test_uuid_auto_generated_unique(self):
        e1 = Employee.objects.create(salon=self.salon, first_name="A")
        e2 = Employee.objects.create(salon=self.salon, first_name="B")
        self.assertNotEqual(e1.id, e2.id)


class EmployeeFieldMetaTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")

    def test_db_table(self):
        self.assertEqual(Employee._meta.db_table, "employees")

    def test_first_name_max_length(self):
        field = Employee._meta.get_field("first_name")
        self.assertEqual(field.max_length, 100)
        self.assertFalse(field.blank)

    def test_last_name_max_length_blank(self):
        field = Employee._meta.get_field("last_name")
        self.assertEqual(field.max_length, 100)
        self.assertTrue(field.blank)

    def test_phone_max_length_blank(self):
        field = Employee._meta.get_field("phone")
        self.assertEqual(field.max_length, 32)
        self.assertTrue(field.blank)

    def test_email_blank(self):
        field = Employee._meta.get_field("email")
        self.assertTrue(field.blank)

    def test_is_active_default_true(self):
        field = Employee._meta.get_field("is_active")
        self.assertTrue(field.default)

    def test_created_at_auto_now_add(self):
        field = Employee._meta.get_field("created_at")
        self.assertTrue(field.auto_now_add)

    def test_updated_at_auto_now(self):
        field = Employee._meta.get_field("updated_at")
        self.assertTrue(field.auto_now)


class EmployeeStrTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")

    def test_str_first_and_last(self):
        emp = Employee.objects.create(salon=self.salon, first_name="Ivan", last_name="Petrov")
        self.assertEqual(str(emp), "Ivan Petrov")

    def test_str_first_only(self):
        emp = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.assertEqual(str(emp), "Ivan")

    def test_str_strips_whitespace(self):
        emp = Employee.objects.create(
            salon=self.salon, first_name="Ivan", last_name=""
        )
        self.assertEqual(str(emp), "Ivan")
        self.assertNotIn("  ", str(emp))


class EmployeeForeignKeyTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            Employee.objects.create(salon=None, first_name="A")

    def test_cascade_delete_salon(self):
        emp = Employee.objects.create(salon=self.salon, first_name="A")
        salon_id = self.salon.id
        self.salon.delete()
        self.assertFalse(Employee.objects.filter(id=emp.id).exists())
        self.assertFalse(Employee.objects.filter(salon_id=salon_id).exists())

    def test_related_name(self):
        emp = Employee.objects.create(salon=self.salon, first_name="A")
        self.assertIn(emp, self.salon.employees.all())

    def test_multiple_employees_per_salon(self):
        e1 = Employee.objects.create(salon=self.salon, first_name="A")
        e2 = Employee.objects.create(salon=self.salon, first_name="B")
        self.assertEqual(self.salon.employees.count(), 2)

    def test_different_salon_independent(self):
        salon2 = Salon.objects.create(name="S2", slug="s2")
        Employee.objects.create(salon=self.salon, first_name="A")
        Employee.objects.create(salon=salon2, first_name="B")
        self.assertEqual(self.salon.employees.count(), 1)
        self.assertEqual(salon2.employees.count(), 1)


class EmployeeAutoTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")
        self.emp = Employee.objects.create(salon=self.salon, first_name="Ivan")

    def test_created_at_set_on_create(self):
        self.assertIsNotNone(self.emp.created_at)

    def test_updated_at_set_on_create(self):
        self.assertIsNotNone(self.emp.updated_at)

    def test_created_at_does_not_change_on_save(self):
        old = self.emp.created_at
        self.emp.first_name = "Petr"
        self.emp.save()
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.created_at, old)

    def test_updated_at_changes_on_save(self):
        old = self.emp.updated_at
        self.emp.first_name = "Petr"
        self.emp.save()
        self.emp.refresh_from_db()
        self.assertGreaterEqual(self.emp.updated_at, old)


class EmployeeQueriesTest(TestCase):
    def setUp(self):
        self.salon1 = Salon.objects.create(name="S1", slug="s1")
        self.salon2 = Salon.objects.create(name="S2", slug="s2")
        Employee.objects.create(salon=self.salon1, first_name="A", is_active=True)
        Employee.objects.create(salon=self.salon1, first_name="B", is_active=False)
        Employee.objects.create(salon=self.salon2, first_name="C", is_active=True)

    def test_filter_by_salon(self):
        self.assertEqual(Employee.objects.filter(salon=self.salon1).count(), 2)
        self.assertEqual(Employee.objects.filter(salon=self.salon2).count(), 1)

    def test_filter_by_is_active(self):
        self.assertEqual(Employee.objects.filter(is_active=True).count(), 2)
        self.assertEqual(Employee.objects.filter(is_active=False).count(), 1)

    def test_chained_filter(self):
        qs = Employee.objects.filter(salon=self.salon1, is_active=True)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().first_name, "A")


class EmployeeBranchCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")

    def test_create(self):
        link = EmployeeBranch.objects.create(
            employee=self.employee,
            branch=self.branch,
        )
        self.assertEqual(link.employee, self.employee)
        self.assertEqual(link.branch, self.branch)
        self.assertTrue(link.is_active)

    def test_id_is_uuid(self):
        link = EmployeeBranch.objects.create(employee=self.employee, branch=self.branch)
        self.assertIsInstance(link.id, uuid.UUID)
        self.assertTrue(EmployeeBranch._meta.get_field("id").primary_key)

    def test_db_table(self):
        self.assertEqual(EmployeeBranch._meta.db_table, "employee_branches")

    def test_is_active_default_true(self):
        self.assertTrue(EmployeeBranch._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        link = EmployeeBranch.objects.create(employee=self.employee, branch=self.branch)
        self.assertIsNotNone(link.created_at)
        self.assertTrue(EmployeeBranch._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(EmployeeBranch._meta.get_field("updated_at").auto_now)


class EmployeeBranchStrTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")
        self.employee = Employee.objects.create(
            salon=self.salon, first_name="Ivan", last_name="Petrov"
        )

    def test_str(self):
        link = EmployeeBranch.objects.create(employee=self.employee, branch=self.branch)
        self.assertEqual(str(link), "Ivan Petrov → Hub — Downtown")


class EmployeeBranchRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.branch1 = Branch.objects.create(salon=self.salon, name="B1")
        self.branch2 = Branch.objects.create(salon=self.salon, name="B2")
        self.employee1 = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.employee2 = Employee.objects.create(salon=self.salon, first_name="Petr")

    def test_employee_related_name(self):
        link = EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        self.assertIn(link, self.employee1.employee_branches.all())

    def test_branch_related_name(self):
        link = EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        self.assertIn(link, self.branch1.employee_branches.all())

    def test_employee_many_branches(self):
        EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch2)
        self.assertEqual(self.employee1.employee_branches.count(), 2)

    def test_branch_many_employees(self):
        EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        EmployeeBranch.objects.create(employee=self.employee2, branch=self.branch1)
        self.assertEqual(self.branch1.employee_branches.count(), 2)

    def test_cascade_delete_employee(self):
        link = EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        self.employee1.delete()
        self.assertFalse(EmployeeBranch.objects.filter(id=link.id).exists())

    def test_cascade_delete_branch(self):
        link = EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        self.branch1.delete()
        self.assertFalse(EmployeeBranch.objects.filter(id=link.id).exists())

    def test_employee_required(self):
        from django.db import IntegrityError as DBError
        with self.assertRaises(DBError):
            EmployeeBranch.objects.create(employee=None, branch=self.branch1)

    def test_branch_required(self):
        from django.db import IntegrityError as DBError
        with self.assertRaises(DBError):
            EmployeeBranch.objects.create(employee=self.employee1, branch=None)

    def test_unique_constraint_same_pair(self):
        EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        with self.assertRaises(IntegrityError):
            EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)

    def test_unique_constraint_allows_diff_branch(self):
        EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        link2 = EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch2)
        self.assertIsNotNone(link2.id)

    def test_unique_constraint_allows_diff_employee(self):
        EmployeeBranch.objects.create(employee=self.employee1, branch=self.branch1)
        link2 = EmployeeBranch.objects.create(employee=self.employee2, branch=self.branch1)
        self.assertIsNotNone(link2.id)

    def test_unique_constraint_name(self):
        names = {c.name for c in EmployeeBranch._meta.constraints}
        self.assertIn("unique_employee_branch", names)


class EmployeeBranchTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.branch = Branch.objects.create(salon=self.salon, name="B")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.link = EmployeeBranch.objects.create(employee=self.employee, branch=self.branch)

    def test_created_at_unchanged_on_save(self):
        old = self.link.created_at
        self.link.is_active = False
        self.link.save()
        self.link.refresh_from_db()
        self.assertEqual(self.link.created_at, old)

    def test_updated_at_changes_on_save(self):
        old = self.link.updated_at
        self.link.is_active = False
        self.link.save()
        self.link.refresh_from_db()
        self.assertGreaterEqual(self.link.updated_at, old)
