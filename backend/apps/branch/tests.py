import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

# pyrefly: ignore [missing-import]
from apps.tenants.models import Salon
# pyrefly: ignore [missing-import]
from apps.branch.models import Branch

User = get_user_model()


class BranchCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Barber Hub", slug="barber-hub")

    def test_create_branch(self):
        branch = Branch.objects.create(
            salon=self.salon,
            name="Downtown",
            address="123 Main St",
            phone="+1234567890",
        )
        self.assertEqual(branch.salon, self.salon)
        self.assertEqual(branch.name, "Downtown")
        self.assertEqual(branch.address, "123 Main St")
        self.assertEqual(branch.phone, "+1234567890")

    def test_create_branch_minimal(self):
        branch = Branch.objects.create(salon=self.salon, name="Minimal")
        self.assertEqual(branch.address, "")
        self.assertEqual(branch.phone, "")
        self.assertTrue(branch.is_active)

    def test_id_is_uuid(self):
        branch = Branch.objects.create(salon=self.salon, name="Test")
        self.assertIsInstance(branch.id, uuid.UUID)

    def test_id_primary_key(self):
        field = Branch._meta.get_field("id")
        self.assertTrue(field.primary_key)
        self.assertFalse(field.editable)

    def test_uuid_auto_generated(self):
        b1 = Branch.objects.create(salon=self.salon, name="A")
        b2 = Branch.objects.create(salon=self.salon, name="B")
        self.assertNotEqual(b1.id, b2.id)


class BranchFieldConstraintsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")

    def test_name_max_length(self):
        field = Branch._meta.get_field("name")
        self.assertEqual(field.max_length, 255)
        self.assertFalse(field.blank)

    def test_address_max_length(self):
        field = Branch._meta.get_field("address")
        self.assertEqual(field.max_length, 500)
        self.assertTrue(field.blank)

    def test_phone_max_length(self):
        field = Branch._meta.get_field("phone")
        self.assertEqual(field.max_length, 32)
        self.assertTrue(field.blank)

    def test_is_active_default_true(self):
        branch = Branch.objects.create(salon=self.salon, name="Test")
        self.assertTrue(branch.is_active)

    def test_is_active_field_default(self):
        field = Branch._meta.get_field("is_active")
        self.assertTrue(field.default)

    def test_db_table(self):
        self.assertEqual(Branch._meta.db_table, "branches")

    def test_created_at_auto_now_add(self):
        field = Branch._meta.get_field("created_at")
        self.assertTrue(field.auto_now_add)

    def test_updated_at_auto_now(self):
        field = Branch._meta.get_field("updated_at")
        self.assertTrue(field.auto_now)

    def test_created_at_set_on_create(self):
        branch = Branch.objects.create(salon=self.salon, name="T")
        self.assertIsNotNone(branch.created_at)

    def test_updated_at_set_on_create(self):
        branch = Branch.objects.create(salon=self.salon, name="T")
        self.assertIsNotNone(branch.updated_at)


class BranchAutoTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")
        self.branch = Branch.objects.create(salon=self.salon, name="Main")

    def test_created_at_does_not_change_on_save(self):
        old = self.branch.created_at
        self.branch.name = "Updated"
        self.branch.save()
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.created_at, old)

    def test_updated_at_changes_on_save(self):
        old = self.branch.updated_at
        self.branch.name = "Updated"
        self.branch.save()
        self.branch.refresh_from_db()
        self.assertGreaterEqual(self.branch.updated_at, old)


class BranchStrTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Barber Hub", slug="barber-hub")
        self.branch = Branch.objects.create(salon=self.salon, name="Downtown")

    def test_str(self):
        self.assertEqual(str(self.branch), "Barber Hub — Downtown")

    def test_str_reflects_salon_name_change(self):
        self.salon.name = "New Salon"
        self.salon.save()
        self.branch.refresh_from_db()
        self.assertEqual(str(self.branch), "New Salon — Downtown")

    def test_str_reflects_branch_name_change(self):
        self.branch.name = "Uptown"
        self.branch.save()
        self.branch.refresh_from_db()
        self.assertEqual(str(self.branch), "Barber Hub — Uptown")


class BranchForeignKeyTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="S", slug="s")

    def test_salon_fk_related_name(self):
        branch = Branch.objects.create(salon=self.salon, name="B")
        self.assertIn(branch, self.salon.branches.all())

    def test_salon_fk_cascade_delete(self):
        Branch.objects.create(salon=self.salon, name="B")
        salon_id = self.salon.id
        self.salon.delete()
        self.assertEqual(Branch.objects.filter(salon_id=salon_id).count(), 0)

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            Branch.objects.create(salon=None, name="No Salon")

    def test_multiple_branches_per_salon(self):
        b1 = Branch.objects.create(salon=self.salon, name="B1")
        b2 = Branch.objects.create(salon=self.salon, name="B2")
        self.assertEqual(self.salon.branches.count(), 2)


class BranchQueryTest(TestCase):
    def setUp(self):
        self.salon1 = Salon.objects.create(name="S1", slug="s1")
        self.salon2 = Salon.objects.create(name="S2", slug="s2")
        Branch.objects.create(salon=self.salon1, name="A", is_active=True)
        Branch.objects.create(salon=self.salon1, name="B", is_active=False)
        Branch.objects.create(salon=self.salon2, name="C", is_active=True)

    def test_filter_by_salon(self):
        self.assertEqual(Branch.objects.filter(salon=self.salon1).count(), 2)
        self.assertEqual(Branch.objects.filter(salon=self.salon2).count(), 1)

    def test_filter_by_is_active(self):
        self.assertEqual(Branch.objects.filter(is_active=True).count(), 2)
        self.assertEqual(Branch.objects.filter(is_active=False).count(), 1)

    def test_chained_filter(self):
        qs = Branch.objects.filter(salon=self.salon1, is_active=True)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "A")
