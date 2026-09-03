import uuid
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.tenants.models import Salon
from apps.clients.models import Client, LoyaltyLevel


class LoyaltyLevelCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")

    def test_create(self):
        level = LoyaltyLevel.objects.create(
            salon=self.salon,
            name="VIP",
            min_visits=20,
            discount_percent=Decimal("10.00"),
        )
        self.assertEqual(level.salon, self.salon)
        self.assertEqual(level.name, "VIP")
        self.assertEqual(level.min_visits, 20)
        self.assertEqual(level.discount_percent, Decimal("10.00"))
        self.assertTrue(level.is_active)

    def test_create_minimal_defaults(self):
        level = LoyaltyLevel.objects.create(salon=self.salon, name="New")
        self.assertEqual(level.min_visits, 0)
        self.assertEqual(level.discount_percent, Decimal("0"))
        self.assertTrue(level.is_active)

    def test_id_is_uuid(self):
        level = LoyaltyLevel.objects.create(salon=self.salon, name="X")
        self.assertIsInstance(level.id, uuid.UUID)
        self.assertTrue(LoyaltyLevel._meta.get_field("id").primary_key)

    def test_id_not_editable(self):
        self.assertFalse(LoyaltyLevel._meta.get_field("id").editable)

    def test_str(self):
        level = LoyaltyLevel.objects.create(salon=self.salon, name="VIP")
        self.assertEqual(str(level), "VIP")


class LoyaltyLevelMetaTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")

    def test_db_table(self):
        self.assertEqual(LoyaltyLevel._meta.db_table, "loyalty_levels")

    def test_name_max_length(self):
        field = LoyaltyLevel._meta.get_field("name")
        self.assertEqual(field.max_length, 100)
        self.assertFalse(field.blank)

    def test_min_visits_positive_integer(self):
        field = LoyaltyLevel._meta.get_field("min_visits")
        self.assertIsInstance(
            field,
            __import__("django.db.models", fromlist=["PositiveIntegerField"]).PositiveIntegerField,
        )
        self.assertEqual(field.default, 0)

    def test_discount_decimal(self):
        field = LoyaltyLevel._meta.get_field("discount_percent")
        self.assertEqual(field.max_digits, 5)
        self.assertEqual(field.decimal_places, 2)
        self.assertEqual(field.default, 0)

    def test_is_active_default_true(self):
        self.assertTrue(LoyaltyLevel._meta.get_field("is_active").default)

    def test_created_at_auto_now_add(self):
        self.assertTrue(LoyaltyLevel._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(LoyaltyLevel._meta.get_field("updated_at").auto_now)


class LoyaltyLevelRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.salon2 = Salon.objects.create(name="Hub2", slug="hub2")

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            LoyaltyLevel.objects.create(salon=None, name="X")

    def test_salon_cascade(self):
        level = LoyaltyLevel.objects.create(salon=self.salon, name="X")
        self.salon.delete()
        self.assertFalse(LoyaltyLevel.objects.filter(id=level.id).exists())

    def test_related_name(self):
        level = LoyaltyLevel.objects.create(salon=self.salon, name="X")
        self.assertIn(level, self.salon.loyalty_levels.all())

    def test_unique_constraint_same_salon_same_name(self):
        LoyaltyLevel.objects.create(salon=self.salon, name="VIP")
        with self.assertRaises(IntegrityError):
            LoyaltyLevel.objects.create(salon=self.salon, name="VIP")

    def test_unique_constraint_same_name_diff_salon_ok(self):
        LoyaltyLevel.objects.create(salon=self.salon, name="VIP")
        level2 = LoyaltyLevel.objects.create(salon=self.salon2, name="VIP")
        self.assertIsNotNone(level2.id)

    def test_constraint_name(self):
        names = {c.name for c in LoyaltyLevel._meta.constraints}
        self.assertIn("unique_salon_loyalty_level_name", names)

    def test_timestamps(self):
        level = LoyaltyLevel.objects.create(salon=self.salon, name="X")
        old_created = level.created_at
        old_updated = level.updated_at
        level.min_visits = 5
        level.save()
        level.refresh_from_db()
        self.assertEqual(level.created_at, old_created)
        self.assertGreaterEqual(level.updated_at, old_updated)


class ClientCreateTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")

    def test_create(self):
        client = Client.objects.create(
            salon=self.salon,
            first_name="Alex",
            last_name="Smith",
            phone="+79161112233",
            email="alex@test.com",
            notes="Prefers window seat",
        )
        self.assertEqual(client.salon, self.salon)
        self.assertEqual(client.first_name, "Alex")
        self.assertEqual(client.last_name, "Smith")
        self.assertEqual(client.phone, "+79161112233")
        self.assertEqual(client.email, "alex@test.com")
        self.assertEqual(client.notes, "Prefers window seat")
        self.assertTrue(client.is_active)
        self.assertIsNone(client.loyalty_level)

    def test_create_minimal(self):
        client = Client.objects.create(salon=self.salon, first_name="Alex", phone="+1")
        self.assertEqual(client.last_name, "")
        self.assertEqual(client.email, "")
        self.assertEqual(client.notes, "")

    def test_id_is_uuid(self):
        client = Client.objects.create(salon=self.salon, first_name="A", phone="+1")
        self.assertIsInstance(client.id, uuid.UUID)
        self.assertTrue(Client._meta.get_field("id").primary_key)

    def test_str(self):
        client = Client.objects.create(
            salon=self.salon, first_name="Alex", last_name="Smith", phone="+1",
        )
        self.assertEqual(str(client), "Alex Smith")

    def test_str_first_only(self):
        client = Client.objects.create(salon=self.salon, first_name="Alex", phone="+1")
        self.assertEqual(str(client), "Alex")

    def test_str_strips_whitespace(self):
        client = Client.objects.create(salon=self.salon, first_name="Alex", last_name="", phone="+1")
        self.assertEqual(str(client), "Alex")
        self.assertNotIn("  ", str(client))


class ClientFieldMetaTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")

    def test_db_table(self):
        self.assertEqual(Client._meta.db_table, "clients")

    def test_first_name_max_length(self):
        field = Client._meta.get_field("first_name")
        self.assertEqual(field.max_length, 100)
        self.assertFalse(field.blank)

    def test_last_name_max_length_blank(self):
        field = Client._meta.get_field("last_name")
        self.assertEqual(field.max_length, 100)
        self.assertTrue(field.blank)

    def test_phone_max_length(self):
        field = Client._meta.get_field("phone")
        self.assertEqual(field.max_length, 32)
        self.assertFalse(field.blank)

    def test_email_blank(self):
        self.assertTrue(Client._meta.get_field("email").blank)

    def test_notes_blank(self):
        self.assertTrue(Client._meta.get_field("notes").blank)

    def test_is_active_default_true(self):
        self.assertTrue(Client._meta.get_field("is_active").default)

    def test_loyalty_level_null_blank(self):
        field = Client._meta.get_field("loyalty_level")
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_loyalty_level_set_null(self):
        field = Client._meta.get_field("loyalty_level")
        self.assertEqual(field.remote_field.on_delete.__name__, "SET_NULL")

    def test_created_at_auto_now_add(self):
        self.assertTrue(Client._meta.get_field("created_at").auto_now_add)

    def test_updated_at_auto_now(self):
        self.assertTrue(Client._meta.get_field("updated_at").auto_now)


class ClientRelationsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.salon2 = Salon.objects.create(name="Hub2", slug="hub2")
        self.level = LoyaltyLevel.objects.create(salon=self.salon, name="VIP")
        self.client = Client.objects.create(
            salon=self.salon, first_name="Alex", phone="+1",
            loyalty_level=self.level,
        )

    def test_salon_required(self):
        with self.assertRaises(IntegrityError):
            Client.objects.create(salon=None, first_name="A", phone="+1")

    def test_salon_cascade(self):
        self.salon.delete()
        self.assertFalse(Client.objects.filter(id=self.client.id).exists())

    def test_salon_related_name(self):
        self.assertIn(self.client, self.salon.clients.all())

    def test_loyalty_level_related_name(self):
        self.assertIn(self.client, self.level.clients.all())

    def test_loyalty_level_set_null_on_delete(self):
        level_id = self.level.id
        self.level.delete()
        self.client.refresh_from_db()
        self.assertIsNone(self.client.loyalty_level)
        self.assertTrue(Client.objects.filter(id=self.client.id).exists())

    def test_multiple_clients_per_salon(self):
        Client.objects.create(salon=self.salon, first_name="B", phone="+2")
        self.assertEqual(self.salon.clients.count(), 2)

    def test_unique_constraint_same_salon_same_phone(self):
        with self.assertRaises(IntegrityError):
            Client.objects.create(salon=self.salon, first_name="C", phone="+1")

    def test_unique_constraint_same_phone_diff_salon_ok(self):
        c2 = Client.objects.create(salon=self.salon2, first_name="D", phone="+1")
        self.assertIsNotNone(c2.id)

    def test_constraint_name(self):
        names = {c.name for c in Client._meta.constraints}
        self.assertIn("unique_salon_client_phone", names)


class ClientTimestampsTest(TestCase):
    def setUp(self):
        self.salon = Salon.objects.create(name="Hub", slug="hub")
        self.client = Client.objects.create(salon=self.salon, first_name="A", phone="+1")

    def test_created_at_set(self):
        self.assertIsNotNone(self.client.created_at)

    def test_updated_at_set(self):
        self.assertIsNotNone(self.client.updated_at)

    def test_created_at_unchanged_on_save(self):
        old = self.client.created_at
        self.client.notes = "note"
        self.client.save()
        self.client.refresh_from_db()
        self.assertEqual(self.client.created_at, old)

    def test_updated_at_changes_on_save(self):
        old = self.client.updated_at
        self.client.notes = "note"
        self.client.save()
        self.client.refresh_from_db()
        self.assertGreaterEqual(self.client.updated_at, old)
