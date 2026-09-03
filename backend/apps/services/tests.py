import uuid
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.tenants.models import Salon
from apps.employee.models import Employee
from apps.services.models import Service, ServiceCategory, EmployeeService


class ServiceCategoryCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")

    def test_create(self):
        cat = ServiceCategory.objects.create(
            salon=self.salon,
            name="Стрижки",
            description="Все стрижки",
        )
        self.assertEqual(cat.salon, self.salon)
        self.assertEqual(cat.name, "Стрижки")
        self.assertEqual(cat.description, "Все стрижки")
        self.assertTrue(cat.is_active)

    def test_create_minimal(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="Борода")
        self.assertEqual(cat.description, "")
        self.assertTrue(cat.is_active)

    def test_id_is_uuid(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="X")
        self.assertIsInstance(cat.id, uuid.UUID)
        self.assertTrue(ServiceCategory._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(ServiceCategory._meta.get_field("id").editable)

    def test_str(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="Стрижки")
        self.assertEqual(str(cat), "Стрижки")


class ServiceCategoryMetaAndRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")

    def test_db_table(self):
        self.assertEqual(ServiceCategory._meta.db_table, "service_categories")

    def test_name_max_length(self):
        field = ServiceCategory._meta.get_field("name")
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)

    def test_description_blank(self):
        self.assertTrue(ServiceCategory._meta.get_field("description").blank)

    def test_is_active_default_true(self):
        self.assertTrue(ServiceCategory._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        self.assertTrue(ServiceCategory._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(ServiceCategory._meta.get_field("updated_at").auto_now)

    def test_salon_fk_cascade(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="X")
        self.salon.delete()
        self.assertFalse(ServiceCategory.objects.filter(id=cat.id).exists())

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            ServiceCategory.objects.create(salon=None, name="X")

    def test_related_name(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="X")
        self.assertIn(cat, self.salon.service_categories.all())

    def test_multiple_categories_per_salon(self):
        ServiceCategory.objects.create(salon=self.salon, name="A")
        ServiceCategory.objects.create(salon=self.salon, name="B")
        self.assertEqual(self.salon.service_categories.count(), 2)

    def test_created_at_unchanged_on_save(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="X")
        old = cat.created_at
        cat.name = "Y"
        cat.save()
        cat.refresh_from_db()
        self.assertEqual(cat.created_at, old)

    def test_updated_at_changes_on_save(self):
        cat = ServiceCategory.objects.create(salon=self.salon, name="X")
        old = cat.updated_at
        cat.name = "Y"
        cat.save()
        cat.refresh_from_db()
        self.assertGreaterEqual(cat.updated_at, old)


class ServiceCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.category = ServiceCategory.objects.create(salon=self.salon, name="Стрижки")

    def test_create(self):
        service = Service.objects.create(
            salon=self.salon,
            category=self.category,
            name="Мужская стрижка",
            description="Классика",
            price=Decimal("500.00"),
            duration_minutes=45,
        )
        self.assertEqual(service.salon, self.salon)
        self.assertEqual(service.category, self.category)
        self.assertEqual(service.name, "Мужская стрижка")
        self.assertEqual(service.description, "Классика")
        self.assertEqual(service.price, Decimal("500.00"))
        self.assertEqual(service.duration_minutes, 45)
        self.assertTrue(service.is_active)

    def test_id_is_uuid(self):
        s = Service.objects.create(
            salon=self.salon, category=self.category, name="X",
            price=Decimal("100"), duration_minutes=30,
        )
        self.assertIsInstance(s.id, uuid.UUID)

    def test_str(self):
        s = Service.objects.create(
            salon=self.salon, category=self.category, name="Стрижка",
            price=Decimal("100"), duration_minutes=30,
        )
        self.assertEqual(str(s), "Стрижка")

    def test_price_decimal(self):
        s = Service.objects.create(
            salon=self.salon, category=self.category, name="X",
            price=Decimal("99.99"), duration_minutes=30,
        )
        self.assertEqual(s.price, Decimal("99.99"))
        self.assertIsInstance(s.price, Decimal)


class ServiceFieldMetaTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.category = ServiceCategory.objects.create(salon=self.salon, name="C")

    def test_db_table(self):
        self.assertEqual(Service._meta.db_table, "services")

    def test_name_max_length(self):
        field = Service._meta.get_field("name")
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)

    def test_description_blank(self):
        self.assertTrue(Service._meta.get_field("description").blank)

    def test_price_decimal_places(self):
        field = Service._meta.get_field("price")
        self.assertEqual(field.max_digits, 10)
        self.assertEqual(field.decimal_places, 2)

    def test_duration_positive_integer(self):
        field = Service._meta.get_field("duration_minutes")
        self.assertIsInstance(field, __import__("django.db.models", fromlist=["PositiveIntegerField"]).PositiveIntegerField)

    def test_is_active_default_true(self):
        self.assertTrue(Service._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        self.assertTrue(Service._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(Service._meta.get_field("updated_at").auto_now)

    def test_description_can_be_empty(self):
        s = Service.objects.create(
            salon=self.salon, category=self.category, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertEqual(s.description, "")


class ServiceRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.salon2 = Salon.objects.create(name="Hub2", slug="hub2")
        self.cat = ServiceCategory.objects.create(salon=self.salon, name="C")
        self.cat2 = ServiceCategory.objects.create(salon=self.salon2, name="C2")

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            Service.objects.create(
                salon=None, category=self.cat, name="X",
                price=Decimal("1"), duration_minutes=10,
            )

    def test_category_required(self):
        with self.assertRaises(IntegrityError):
            Service.objects.create(
                salon=self.salon, category=None, name="X",
                price=Decimal("1"), duration_minutes=10,
            )

    def test_salon_cascade(self):
        s = Service.objects.create(
            salon=self.salon, category=self.cat, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        self.salon.delete()
        self.assertFalse(Service.objects.filter(id=s.id).exists())

    def test_category_cascade(self):
        s = Service.objects.create(
            salon=self.salon, category=self.cat, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        self.cat.delete()
        self.assertFalse(Service.objects.filter(id=s.id).exists())

    def test_salon_related_name(self):
        s = Service.objects.create(
            salon=self.salon, category=self.cat, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertIn(s, self.salon.services.all())

    def test_category_related_name(self):
        s = Service.objects.create(
            salon=self.salon, category=self.cat, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertIn(s, self.cat.services.all())

    def test_service_belongs_to_same_salon_category(self):
        s = Service.objects.create(
            salon=self.salon, category=self.cat, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        self.assertEqual(s.salon, s.category.salon)

    def test_timestamps(self):
        s = Service.objects.create(
            salon=self.salon, category=self.cat, name="X",
            price=Decimal("1"), duration_minutes=10,
        )
        old_created = s.created_at
        old_updated = s.updated_at
        s.price = Decimal("2")
        s.save()
        s.refresh_from_db()
        self.assertEqual(s.created_at, old_created)
        self.assertGreaterEqual(s.updated_at, old_updated)


class EmployeeServiceCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.category = ServiceCategory.objects.create(salon=self.salon, name="C")
        self.service = Service.objects.create(
            salon=self.salon, category=self.category, name="S",
            price=Decimal("100"), duration_minutes=30,
        )

    def test_create(self):
        link = EmployeeService.objects.create(
            employee=self.employee,
            service=self.service,
        )
        self.assertEqual(link.employee, self.employee)
        self.assertEqual(link.service, self.service)
        self.assertTrue(link.is_active)

    def test_id_is_uuid(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        self.assertIsInstance(link.id, uuid.UUID)
        self.assertTrue(EmployeeService._meta.get_field("id").primary_key)

    def test_db_table(self):
        self.assertEqual(EmployeeService._meta.db_table, "employee_services")

    def test_is_active_default_true(self):
        self.assertTrue(EmployeeService._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        self.assertTrue(EmployeeService._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(EmployeeService._meta.get_field("updated_at").auto_now)

    def test_str(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        self.assertEqual(str(link), "Ivan → S")


class EmployeeServiceRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.employee = Employee.objects.create(salon=self.salon, first_name="Ivan")
        self.employee2 = Employee.objects.create(salon=self.salon, first_name="Petr")
        self.category = ServiceCategory.objects.create(salon=self.salon, name="C")
        self.service = Service.objects.create(
            salon=self.salon, category=self.category, name="S1",
            price=Decimal("100"), duration_minutes=30,
        )
        self.service2 = Service.objects.create(
            salon=self.salon, category=self.category, name="S2",
            price=Decimal("200"), duration_minutes=60,
        )

    def test_employee_related_name(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        self.assertIn(link, self.employee.employee_services.all())

    def test_service_related_name(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        self.assertIn(link, self.service.employee_services.all())

    def test_employee_many_services(self):
        EmployeeService.objects.create(employee=self.employee, service=self.service)
        EmployeeService.objects.create(employee=self.employee, service=self.service2)
        self.assertEqual(self.employee.employee_services.count(), 2)

    def test_service_many_employees(self):
        EmployeeService.objects.create(employee=self.employee, service=self.service)
        EmployeeService.objects.create(employee=self.employee2, service=self.service)
        self.assertEqual(self.service.employee_services.count(), 2)

    def test_employee_required(self):
        with self.assertRaises(IntegrityError):
            EmployeeService.objects.create(employee=None, service=self.service)

    def test_service_required(self):
        with self.assertRaises(IntegrityError):
            EmployeeService.objects.create(employee=self.employee, service=None)

    def test_cascade_delete_employee(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        self.employee.delete()
        self.assertFalse(EmployeeService.objects.filter(id=link.id).exists())

    def test_cascade_delete_service(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        self.service.delete()
        self.assertFalse(EmployeeService.objects.filter(id=link.id).exists())

    def test_unique_constraint_same_pair(self):
        EmployeeService.objects.create(employee=self.employee, service=self.service)
        with self.assertRaises(IntegrityError):
            EmployeeService.objects.create(employee=self.employee, service=self.service)

    def test_unique_constraint_allows_diff_service(self):
        EmployeeService.objects.create(employee=self.employee, service=self.service)
        link2 = EmployeeService.objects.create(employee=self.employee, service=self.service2)
        self.assertIsNotNone(link2.id)

    def test_unique_constraint_allows_diff_employee(self):
        EmployeeService.objects.create(employee=self.employee, service=self.service)
        link2 = EmployeeService.objects.create(employee=self.employee2, service=self.service)
        self.assertIsNotNone(link2.id)

    def test_unique_constraint_name(self):
        names = {c.name for c in EmployeeService._meta.constraints}
        self.assertIn("unique_employee_service", names)

    def test_timestamps(self):
        link = EmployeeService.objects.create(employee=self.employee, service=self.service)
        old_created = link.created_at
        old_updated = link.updated_at
        link.is_active = False
        link.save()
        link.refresh_from_db()
        self.assertEqual(link.created_at, old_created)
        self.assertGreaterEqual(link.updated_at, old_updated)
