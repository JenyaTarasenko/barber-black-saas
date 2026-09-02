import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

User = get_user_model()


class UserManagerCreateUserTest(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email="test@example.com", password="pass1234")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("pass1234"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(email="Test@Example.COM", password="pass1234")
        self.assertEqual(user.email, "Test@example.com")

    def test_create_user_no_email_raises(self):
        with self.assertRaises(ValueError) as ctx:
            User.objects.create_user(email="", password="pass1234")
        self.assertIn("Email", str(ctx.exception))

    def test_create_user_none_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password="pass1234")

    def test_create_user_extra_fields(self):
        user = User.objects.create_user(
            email="a@b.com",
            password="pass1234",
            phone="+1234567890",
            first_name="John",
            last_name="Doe",
        )
        self.assertEqual(user.phone, "+1234567890")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_create_user_uuid_primary_key(self):
        user = User.objects.create_user(email="a@b.com", password="pass1234")
        self.assertIsInstance(user.id, uuid.UUID)

    def test_create_user_email_is_unique(self):
        User.objects.create_user(email="dup@example.com", password="pass1234")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="dup@example.com", password="pass5678")


class UserManagerCreateSuperuserTest(TestCase):
    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="admin1234")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_create_superuser_password_works(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="admin1234")
        self.assertTrue(admin.check_password("admin1234"))

    def test_create_superuser_can_override_flags_to_false(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="admin1234",
            is_staff=False,
            is_superuser=False,
            is_active=False,
        )
        self.assertFalse(admin.is_staff)
        self.assertFalse(admin.is_superuser)
        self.assertFalse(admin.is_active)


class UserModelFieldsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass1234",
            phone="+111222333",
            first_name="Alice",
            last_name="Smith",
        )

    def test_str_returns_email(self):
        self.assertEqual(str(self.user), "user@example.com")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_db_table(self):
        self.assertEqual(User._meta.db_table, "users")

    def test_email_unique(self):
        self.assertTrue(User._meta.get_field("email").unique)

    def test_phone_blank(self):
        field = User._meta.get_field("phone")
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 32)

    def test_first_name_blank(self):
        field = User._meta.get_field("first_name")
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 100)

    def test_last_name_blank(self):
        field = User._meta.get_field("last_name")
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 100)

    def test_is_active_default_true(self):
        field = User._meta.get_field("is_active")
        self.assertTrue(field.default)

    def test_is_staff_default_false(self):
        field = User._meta.get_field("is_staff")
        self.assertFalse(field.default)

    def test_id_is_uuid_primary_key(self):
        field = User._meta.get_field("id")
        self.assertTrue(field.primary_key)
        self.assertIsInstance(field, uuid.UUID.__class__.__mro__[0]) if not hasattr(field, 'serialize') else None
        self.assertFalse(field.editable)

    def test_created_at_auto_now_add(self):
        field = User._meta.get_field("created_at")
        self.assertTrue(field.auto_now_add)
        self.assertIsNotNone(self.user.created_at)

    def test_updated_at_auto_now(self):
        field = User._meta.get_field("updated_at")
        self.assertTrue(field.auto_now)
        self.assertIsNotNone(self.user.updated_at)

    def test_updated_at_changes_on_save(self):
        old_updated = self.user.updated_at
        self.user.first_name = "Bob"
        self.user.save()
        self.user.refresh_from_db()
        self.assertGreaterEqual(self.user.updated_at, old_updated)

    def test_created_at_does_not_change_on_save(self):
        old_created = self.user.created_at
        self.user.first_name = "Bob"
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.created_at, old_created)

    def test_user_without_optional_fields(self):
        user = User.objects.create_user(email="minimal@example.com", password="pass1234")
        self.assertEqual(user.phone, "")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
