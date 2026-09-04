from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.serializers import UserSerializer

User = get_user_model()


class RegisterViewTest(TestCase):
    """Tests for POST /api/accounts/register/."""

    URL = "/api/accounts/register/"

    VALID_DATA = {
        "email": "new@example.com",
        "password": "securepass123",
        "first_name": "John",
        "last_name": "Doe",
    }

    def setUp(self):
        self.client = APIClient()

    def test_successful_registration(self):
        response = self.client.post(self.URL, self.VALID_DATA, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertIn("id", response.data)

    def test_user_created_in_db(self):
        self.client.post(self.URL, self.VALID_DATA, format="json")
        user = User.objects.get(email="new@example.com")
        self.assertTrue(user.check_password("securepass123"))

    def test_password_not_in_response(self):
        response = self.client.post(self.URL, self.VALID_DATA, format="json")
        self.assertNotIn("password", response.data)

    def test_password_is_hashed_in_db(self):
        self.client.post(self.URL, self.VALID_DATA, format="json")
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.password.startswith(self.VALID_DATA["password"]))

    def test_invalid_email_returns_400(self):
        data = {**self.VALID_DATA, "email": "bad-email"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_returns_400(self):
        User.objects.create_user(email="dup@example.com", password="pass1234")
        data = {**self.VALID_DATA, "email": "dup@example.com"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_password_returns_400(self):
        data = {**self.VALID_DATA, "password": "short"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields_returns_400(self):
        response = self.client.post(self.URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeViewTest(TestCase):
    """Tests for GET/PUT/PATCH/DELETE /api/accounts/me/."""

    URL = "/api/accounts/me/"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass1234",
            first_name="Alice",
            last_name="Smith",
            phone="+111222333",
        )

    # --- GET ---

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "user@example.com")
        self.assertEqual(response.data["first_name"], "Alice")

    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.URL)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_profile_returns_all_read_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.URL)
        self.assertIn("id", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        self.assertIn("is_active", response.data)

    # --- PATCH ---

    def test_patch_first_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.URL, {"first_name": "Bob"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Bob")

    def test_patch_last_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.URL, {"last_name": "Jones"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, "Jones")

    def test_patch_phone(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.URL, {"phone": "+999888777"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+999888777")

    def test_patch_read_only_fields_ignored(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.URL,
            {"email": "hacked@example.com", "is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "user@example.com")
        self.assertTrue(self.user.is_active)

    # --- PUT ---

    def test_put_update_profile(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "phone": "+555666777",
            "first_name": "Updated",
            "last_name": "User",
        }
        response = self.client.put(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.phone, "+555666777")

    def test_put_unauthenticated_returns_401(self):
        response = self.client.put(
            self.URL,
            {"phone": "", "first_name": "", "last_name": ""},
            format="json",
        )
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class ChangePasswordViewTest(TestCase):
    """Tests for POST /api/accounts/change-password/."""

    URL = "/api/accounts/change-password/"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="oldpass123",
        )
        self.client.force_authenticate(user=self.user)

    def test_successful_password_change(self):
        data = {"old_password": "oldpass123", "new_password": "newpass456"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))
        self.assertFalse(self.user.check_password("oldpass123"))

    def test_wrong_old_password_returns_400(self):
        data = {"old_password": "wrongpass", "new_password": "newpass456"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_new_password_returns_400(self):
        data = {"old_password": "oldpass123", "new_password": "oldpass123"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_new_password_returns_400(self):
        data = {"old_password": "oldpass123", "new_password": "short"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        data = {"old_password": "oldpass123", "new_password": "newpass456"}
        response = self.client.post(self.URL, data, format="json")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_response_detail_message(self):
        data = {"old_password": "oldpass123", "new_password": "newpass456"}
        response = self.client.post(self.URL, data, format="json")
        self.assertEqual(response.data["detail"], "Password changed successfully.")
