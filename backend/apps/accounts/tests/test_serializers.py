from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from rest_framework.test import APIRequestFactory

from apps.accounts.serializers import (
    ChangePasswordSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class UserRegisterSerializerTest(TestCase):
    """Tests for UserRegisterSerializer."""

    VALID_DATA = {
        "email": "new@example.com",
        "password": "securepass123",
        "phone": "+1234567890",
        "first_name": "John",
        "last_name": "Doe",
    }

    def test_valid_data(self):
        serializer = UserRegisterSerializer(data=self.VALID_DATA)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_user(self):
        serializer = UserRegisterSerializer(data=self.VALID_DATA)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("securepass123"))
        self.assertEqual(user.phone, "+1234567890")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_email_required(self):
        data = {**self.VALID_DATA, "email": ""}
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_invalid_email_format(self):
        data = {**self.VALID_DATA, "email": "not-an-email"}
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_duplicate_email(self):
        User.objects.create_user(email="dup@example.com", password="pass1234")
        data = {**self.VALID_DATA, "email": "dup@example.com"}
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_required(self):
        data = {k: v for k, v in self.VALID_DATA.items() if k != "password"}
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_too_short(self):
        data = {**self.VALID_DATA, "password": "short"}
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_password_write_only(self):
        serializer = UserRegisterSerializer(data=self.VALID_DATA)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        output = UserSerializer(user).data
        self.assertNotIn("password", output)


class UserSerializerTest(TestCase):
    """Tests for UserSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass1234",
            phone="+999888777",
            first_name="Alice",
            last_name="Smith",
        )

    def test_read_fields(self):
        serializer = UserSerializer(self.user)
        data = serializer.data
        expected_fields = {
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_active",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_read_only_fields_cannot_be_updated(self):
        data = {
            "id": "00000000-0000-0000-0000-000000000000",
            "email": "hacked@example.com",
            "is_active": False,
            "phone": "+111222333",
            "first_name": "Bob",
            "last_name": "Jones",
        }
        serializer = UserSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.email, "user@example.com")
        self.assertTrue(updated.is_active)

    def test_writable_fields(self):
        data = {
            "phone": "+111222333",
            "first_name": "Bob",
            "last_name": "Jones",
        }
        serializer = UserSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.phone, "+111222333")
        self.assertEqual(updated.first_name, "Bob")
        self.assertEqual(updated.last_name, "Jones")


class ChangePasswordSerializerTest(TestCase):
    """Tests for ChangePasswordSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="oldpass123",
        )
        self.factory = APIRequestFactory()

    def _get_serializer(self, data):
        request = self.factory.post("/", data)
        request.user = self.user
        return ChangePasswordSerializer(data=data, context={"request": request})

    def test_valid_change(self):
        serializer = self._get_serializer(
            {"old_password": "oldpass123", "new_password": "newpass456"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_wrong_old_password(self):
        serializer = self._get_serializer(
            {"old_password": "wrongpass", "new_password": "newpass456"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

    def test_same_new_and_old_password(self):
        serializer = self._get_serializer(
            {"old_password": "oldpass123", "new_password": "oldpass123"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)

    def test_new_password_too_short(self):
        serializer = self._get_serializer(
            {"old_password": "oldpass123", "new_password": "short"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_password", serializer.errors)

    def test_fields_are_write_only(self):
        serializer = self._get_serializer(
            {"old_password": "oldpass123", "new_password": "newpass456"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("old_password", serializer.data)
        self.assertNotIn("new_password", serializer.data)
