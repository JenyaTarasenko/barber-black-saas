import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.tenants.models import Role, Salon, SalonMembership

User = get_user_model()


class SalonModelTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(
            name="Barber Studio",
            slug="barber-studio",
            phone="+1234567890",
            email="info@barber.com",
        )

    def test_str_returns_name(self):
        self.assertEqual(str(self.salon), "Barber Studio")

    def test_id_is_uuid(self):
        self.assertIsInstance(self.salon.id, uuid.UUID)
        self.assertTrue(self.salon._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(self.salon._meta.get_field("id").editable)

    def test_db_table(self):
        self.assertEqual(Salon._meta.db_table, "salons")

    def test_slug_unique(self):
        self.assertTrue(Salon._meta.get_field("slug").unique)

    def test_slug_is_indexed(self):
        self.assertTrue(Salon._meta.get_field("slug").db_index)

    def test_phone_blank(self):
        field = Salon._meta.get_field("phone")
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 32)

    def test_email_blank(self):
        self.assertTrue(Salon._meta.get_field("email").blank)

    def test_is_active_default_true(self):
        self.assertTrue(self.salon.is_active)

    def test_created_at_auto_now_add(self):
        self.assertIsNotNone(self.salon.created_at)
        self.assertTrue(Salon._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(Salon._meta.get_field("updated_at").auto_now)

    def test_updated_at_changes_on_save(self):
        old = self.salon.updated_at
        self.salon.name = "New Name"
        self.salon.save()
        self.salon.refresh_from_db()
        self.assertGreaterEqual(self.salon.updated_at, old)

    def test_created_at_unchanged_on_save(self):
        old = self.salon.created_at
        self.salon.name = "New Name"
        self.salon.save()
        self.salon.refresh_from_db()
        self.assertEqual(self.salon.created_at, old)

    def test_slug_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            Salon.objects.create(name="Duplicate", slug="barber-studio")

    def test_minimal_salon(self):
        s = Salon.objects.create(name="Minimal", slug="minimal")
        self.assertEqual(s.phone, "")
        self.assertEqual(s.email, "")


class RoleModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            code=Role.OWNER,
            name="Owner",
            description="Salon owner",
        )

    def test_str_returns_name(self):
        self.assertEqual(str(self.role), "Owner")

    def test_id_is_uuid(self):
        self.assertIsInstance(self.role.id, uuid.UUID)
        self.assertTrue(self.role._meta.get_field("id").primary_key)

    def test_db_table(self):
        self.assertEqual(Role._meta.db_table, "roles")

    def test_code_unique(self):
        self.assertTrue(Role._meta.get_field("code").unique)

    def test_code_max_length(self):
        self.assertEqual(Role._meta.get_field("code").max_length, 50)

    def test_name_max_length(self):
        self.assertEqual(Role._meta.get_field("name").max_length, 100)

    def test_description_blank(self):
        self.assertTrue(Role._meta.get_field("description").blank)

    def test_code_choices(self):
        expected = {
            "PLATFORM_ADMIN",
            "OWNER",
            "BRANCH_ADMIN",
            "MASTER",
        }
        codes = {c[0] for c in Role.ROLE_CHOICES}
        self.assertEqual(codes, expected)

    def test_code_duplicate_raises(self):
        with self.assertRaises(IntegrityError):
            Role.objects.create(code=Role.OWNER, name="Another Owner")

    def test_role_constants(self):
        self.assertEqual(Role.PLATFORM_ADMIN, "PLATFORM_ADMIN")
        self.assertEqual(Role.OWNER, "OWNER")
        self.assertEqual(Role.BRANCH_ADMIN, "BRANCH_ADMIN")
        self.assertEqual(Role.MASTER, "MASTER")

    def test_description_can_be_empty(self):
        r = Role.objects.create(code=Role.MASTER, name="Master")
        self.assertEqual(r.description, "")


class SalonMembershipModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="pass1234")
        self.salon = Salon.objects.create(name="Test Salon", slug="test-salon")
        self.role = Role.objects.create(code=Role.OWNER, name="Owner")
        self.membership = SalonMembership.objects.create(
            user=self.user,
            salon=self.salon,
            role=self.role,
        )

    def test_str(self):
        expected = "user@test.com → Test Salon (OWNER)"
        self.assertEqual(str(self.membership), expected)

    def test_id_is_uuid(self):
        self.assertIsInstance(self.membership.id, uuid.UUID)

    def test_db_table(self):
        self.assertEqual(SalonMembership._meta.db_table, "salon_memberships")

    def test_is_active_default_true(self):
        self.assertTrue(self.membership.is_active)

    def test_user_foreign_key(self):
        field = SalonMembership._meta.get_field("user")
        self.assertEqual(field.related_model, User)
        self.assertEqual(field.remote_field.on_delete.__name__, "CASCADE")

    def test_user_related_name(self):
        self.assertIn(self.membership, self.user.salon_memberships.all())

    def test_salon_foreign_key(self):
        field = SalonMembership._meta.get_field("salon")
        self.assertEqual(field.related_model, Salon)
        self.assertEqual(field.remote_field.on_delete.__name__, "CASCADE")

    def test_salon_related_name(self):
        self.assertIn(self.membership, self.salon.memberships.all())

    def test_role_foreign_key(self):
        field = SalonMembership._meta.get_field("role")
        self.assertEqual(field.related_model, Role)
        self.assertEqual(field.remote_field.on_delete.__name__, "PROTECT")

    def test_role_related_name(self):
        self.assertIn(self.membership, self.role.memberships.all())

    def test_unique_user_salon_constraint(self):
        with self.assertRaises(IntegrityError):
            SalonMembership.objects.create(
                user=self.user,
                salon=self.salon,
                role=self.role,
            )

    def test_same_user_different_salon_ok(self):
        salon2 = Salon.objects.create(name="Salon 2", slug="salon-2")
        m2 = SalonMembership.objects.create(
            user=self.user, salon=salon2, role=self.role,
        )
        self.assertNotEqual(self.membership.salon, m2.salon)

    def test_different_user_same_salon_ok(self):
        user2 = User.objects.create_user(email="user2@test.com", password="pass1234")
        m2 = SalonMembership.objects.create(
            user=user2, salon=self.salon, role=self.role,
        )
        self.assertNotEqual(self.membership.user, m2.user)

    def test_created_at_auto_now_add(self):
        self.assertIsNotNone(self.membership.created_at)

    def test_updated_at_auto_now(self):
        self.assertTrue(SalonMembership._meta.get_field("updated_at").auto_now)

    def test_delete_user_cascades(self):
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(SalonMembership.objects.filter(user_id=user_id).exists())

    def test_delete_salon_cascades(self):
        salon_id = self.salon.id
        self.salon.delete()
        self.assertFalse(SalonMembership.objects.filter(salon_id=salon_id).exists())

    def test_delete_role_protected(self):
        from django.db import IntegrityError as DBIntegrityError
        try:
            self.role.delete()
        except Exception:
            pass
        self.assertTrue(Role.objects.filter(id=self.role.id).exists())
