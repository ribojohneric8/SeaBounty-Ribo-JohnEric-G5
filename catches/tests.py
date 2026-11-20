from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from stalls.models import SeafoodCategory, Stall

from .models import CatchUpdate

PW = "Tide&Salt2026"


class CatchUpdateTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer@x.com", PW, full_name="Bea Buyer", role="BUYER")
        self.vendor = User.objects.create_user("vendor@x.com", PW, full_name="Vic Vendor", role="VENDOR")
        self.vendor2 = User.objects.create_user("vendor2@x.com", PW, full_name="Val Vendor", role="VENDOR")
        self.admin = User.objects.create_superuser("admin@x.com", PW, full_name="Ann Admin")
        self.stall = Stall.objects.create(owner=self.vendor, stall_name="Vic's Crabs", location="Santa Fe Port")
        self.other = Stall.objects.create(owner=self.vendor2, stall_name="Val's Fish", location="Madridejos Pier")
        self.closed = Stall.objects.create(owner=self.vendor, stall_name="Closed", location="Old Pier area", is_active=False)
        self.crab = SeafoodCategory.objects.get(name="Crab")
        self.tuna = SeafoodCategory.objects.get(name="Tuna")
        self.update = CatchUpdate.objects.create(stall=self.stall, category=self.crab, posted_by=self.vendor, price_per_kg="450.00")

    def post(self, **over):
        d = {"stall": self.stall.pk, "category": self.tuna.pk, "price_per_kg": "380.50"}
        d.update(over)
        return self.client.post(reverse("catches:create"), d)

    def test_login_required(self):
        for name, args in [("list", []), ("mine", []), ("create", []), ("edit", [self.update.pk]), ("delete", [self.update.pk])]:
            r = self.client.get(reverse(f"catches:{name}", args=args))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/login/", r.url)

    def test_vendor_creates_update_linked_to_self(self):
        self.client.force_login(self.vendor)
        r = self.post()
        self.assertRedirects(r, reverse("catches:mine"))
        u = CatchUpdate.objects.get(category=self.tuna)
        self.assertEqual((u.posted_by, u.stall, u.price_per_kg), (self.vendor, self.stall, Decimal("380.50")))

    def test_buyer_and_admin_cannot_post(self):
        for user in (self.buyer, self.admin):
            self.client.force_login(user)
            self.post()
        self.assertEqual(CatchUpdate.objects.count(), 1)

    def test_price_validation(self):
        self.client.force_login(self.vendor)
        for bad in ("0", "-5", "abc", "", "999999"):
            self.post(price_per_kg=bad)
        self.assertEqual(CatchUpdate.objects.count(), 1)
        self.assertContains(self.post(price_per_kg="0"), "greater than zero")

    def test_database_rejects_non_positive_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CatchUpdate.objects.create(stall=self.stall, category=self.tuna, posted_by=self.vendor, price_per_kg=0)

    def test_cannot_post_to_someone_elses_or_closed_stall(self):
        self.client.force_login(self.vendor)
        self.post(stall=self.other.pk)
        self.post(stall=self.closed.pk)
        self.assertEqual(CatchUpdate.objects.count(), 1)

    def test_edit_by_owner_changes_price_not_stall(self):
        self.client.force_login(self.vendor)
        self.client.post(reverse("catches:edit", args=[self.update.pk]),
                         {"stall": self.other.pk, "category": self.crab.pk, "price_per_kg": "500"})
        self.update.refresh_from_db()
        self.assertEqual(self.update.price_per_kg, Decimal("500.00"))
        self.assertEqual(self.update.stall, self.stall)

    def test_other_vendor_cannot_edit_or_delete(self):
        self.client.force_login(self.vendor2)
        self.client.post(reverse("catches:edit", args=[self.update.pk]), {"stall": self.stall.pk, "category": self.crab.pk, "price_per_kg": "1"})
        self.client.post(reverse("catches:delete", args=[self.update.pk]))
        self.update.refresh_from_db()
        self.assertEqual(self.update.price_per_kg, Decimal("450.00"))

    def test_owner_and_admin_can_delete(self):
        self.client.force_login(self.vendor)
        self.client.post(reverse("catches:delete", args=[self.update.pk]))
        self.assertEqual(CatchUpdate.objects.count(), 0)
        u = CatchUpdate.objects.create(stall=self.stall, category=self.crab, posted_by=self.vendor, price_per_kg=10)
        self.client.force_login(self.admin)
        self.client.post(reverse("catches:delete", args=[u.pk]))
        self.assertEqual(CatchUpdate.objects.count(), 0)

    def test_search_and_filter(self):
        CatchUpdate.objects.create(stall=self.other, category=self.tuna, posted_by=self.vendor2, price_per_kg=300)
        self.client.force_login(self.buyer)
        r = self.client.get(reverse("catches:list"), {"q": "tuna"})
        self.assertContains(r, "Val&#x27;s Fish")
        self.assertNotContains(r, "Vic&#x27;s Crabs")
        r = self.client.get(reverse("catches:list"), {"category": self.crab.pk})
        self.assertContains(r, "Vic&#x27;s Crabs")
        self.assertNotContains(r, "Val&#x27;s Fish")

    def test_closed_stall_updates_hidden_from_search(self):
        CatchUpdate.objects.create(stall=self.closed, category=self.tuna, posted_by=self.vendor, price_per_kg=100)
        self.client.force_login(self.buyer)
        self.assertNotContains(self.client.get(reverse("catches:list")), "Closed")

    def test_my_updates_only_shows_own(self):
        CatchUpdate.objects.create(stall=self.other, category=self.tuna, posted_by=self.vendor2, price_per_kg=300)
        self.client.force_login(self.vendor)
        r = self.client.get(reverse("catches:mine"))
        self.assertContains(r, "Vic&#x27;s Crabs")
        self.assertNotContains(r, "Val&#x27;s Fish")
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("catches:mine")).status_code, 302)

    def test_deleting_stall_cascades_to_updates(self):
        self.stall.delete()
        self.assertEqual(CatchUpdate.objects.count(), 0)

    def test_dashboards_and_stall_detail_show_updates(self):
        self.client.force_login(self.buyer)
        self.assertContains(self.client.get(reverse("accounts:buyer_dashboard")), "450.00")
        self.assertContains(self.client.get(reverse("stalls:detail", args=[self.stall.pk])), "450.00")
        self.client.force_login(self.vendor)
        self.assertContains(self.client.get(reverse("accounts:vendor_dashboard")), "450.00")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("accounts:admin_dashboard")), "catch updates")

    def test_vendor_without_open_stall_is_sent_to_create_one(self):
        newbie = User.objects.create_user("new@x.com", PW, full_name="New", role="VENDOR")
        self.client.force_login(newbie)
        self.assertRedirects(self.client.get(reverse("catches:create")), reverse("stalls:create"), fetch_redirect_response=False)
