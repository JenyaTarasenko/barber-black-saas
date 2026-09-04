from django.test import TestCase
from django.urls import resolve, reverse

from apps.accounts.views import ChangePasswordView, MeView, RegisterView


class URLReverseTest(TestCase):
    """Tests for URL reversing with django.urls.reverse."""

    def test_register_url(self):
        url = reverse("register")
        self.assertEqual(url, "/api/accounts/register/")

    def test_me_url(self):
        url = reverse("me")
        self.assertEqual(url, "/api/accounts/me/")

    def test_change_password_url(self):
        url = reverse("change-password")
        self.assertEqual(url, "/api/accounts/change-password/")


class URLResolveTest(TestCase):
    """Tests for URL resolving with django.urls.resolve."""

    def test_register_resolves_to_register_view(self):
        match = resolve("/api/accounts/register/")
        self.assertEqual(match.func.cls, RegisterView)

    def test_me_resolves_to_me_view(self):
        match = resolve("/api/accounts/me/")
        self.assertEqual(match.func.cls, MeView)

    def test_change_password_resolves_to_change_password_view(self):
        match = resolve("/api/accounts/change-password/")
        self.assertEqual(match.func.cls, ChangePasswordView)
