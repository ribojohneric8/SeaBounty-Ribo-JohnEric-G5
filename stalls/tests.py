from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import SeafoodCategory, Stall

PW = "Tide&Salt2026"


class StallTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer@x.com", PW, full_name="Bea Buyer", role="BUYER")
        self.vendor = User.objects.create_user("vendor@x.com", PW, full_name="Vic Vendor", role="VENDOR")
        self.vendor2 = User.objects.create_user("vendor2@x.com", PW, full_name="Val Vendor", role="VENDOR")
        self.admin = User.objects.create_superuser("admin@x.com", PW, full_name="Ann Admin")
        self.stall = Stall.objects.create(owner=self.vendor, stall_name="Vic's Crabs", location="Santa Fe Port")
        self.closed = Stall.objects.create(owner=self.vendor, stall_name="Closed Stall", location="Madridejos Pier", is_active=False)

    def data(self, **over):
        d = {"stall_name": "Blue Wave", "location": "Bantayan Market", "operating_hours": "5-11 AM", "is_active": "on"}
        d.update(over)
        return d

    def test_categories_are_seeded(self):
        self.assertTrue(SeafoodCategory.objects.filter(name="Crab").exists())

    def test_login_required_everywhere(self):
        for name, args in [("list", []), ("mine", []), ("create", []), ("detail", [self.stall.pk]),
                           ("edit", [self.stall.pk]), ("delete", [self.stall.pk])]:
            r = self.client.get(reverse(f"stalls:{name}", args=args))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/login/", r.url)

    def test_vendor_can_create_stall_linked_to_self(self):
        self.client.force_login(self.vendor)
        r = self.client.post(reverse("stalls:create"), self.data())
        stall = Stall.objects.get(stall_name="Blue Wave")
        self.assertRedirects(r, reverse("stalls:detail", args=[stall.pk]))
        self.assertEqual(stall.owner, self.vendor)

    def test_buyer_and_admin_cannot_create_stall(self):
        for user in (self.buyer, self.admin):
            self.client.force_login(user)
            r = self.client.post(reverse("stalls:create"), self.data())
            self.assertEqual(r.status_code, 302)
        self.assertFalse(Stall.objects.filter(stall_name="Blue Wave").exists())

    def test_validation_duplicate_name_case_insensitive(self):
        self.client.force_login(self.vendor)
        r = self.client.post(reverse("stalls:create"), self.data(stall_name="VIC'S CRABS"))
        self.assertContains(r, "already exists")

    def test_validation_required_and_short_values(self):
        self.client.force_login(self.vendor)
        r = self.client.post(reverse("stalls:create"), self.data(stall_name="", location=""))
        self.assertContains(r, "This field is required")
        r = self.client.post(reverse("stalls:create"), self.data(location="abc"))
        self.assertContains(r, "more specific location")

    def test_vendor_cannot_edit_or_delete_other_vendors_stall(self):
        self.client.force_login(self.vendor2)
        self.client.post(reverse("stalls:edit", args=[self.stall.pk]), self.data(stall_name="Hijacked"))
        self.client.post(reverse("stalls:delete", args=[self.stall.pk]))
        self.stall.refresh_from_db()
        self.assertEqual(self.stall.stall_name, "Vic's Crabs")

    def test_owner_can_update_and_delete(self):
        self.client.force_login(self.vendor)
        self.client.post(reverse("stalls:edit", args=[self.stall.pk]), self.data(stall_name="Vic's Best Crabs"))
        self.stall.refresh_from_db()
        self.assertEqual(self.stall.stall_name, "Vic's Best Crabs")
        self.client.post(reverse("stalls:delete", args=[self.stall.pk]))
        self.assertFalse(Stall.objects.filter(pk=self.stall.pk).exists())

    def test_admin_can_delete_any_stall(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("stalls:delete", args=[self.stall.pk]))
        self.assertFalse(Stall.objects.filter(pk=self.stall.pk).exists())

    def test_closed_stalls_hidden_from_buyers_but_not_admin(self):
        self.client.force_login(self.buyer)
        self.assertNotContains(self.client.get(reverse("stalls:list")), "Closed Stall")
        self.assertEqual(self.client.get(reverse("stalls:detail", args=[self.closed.pk])).status_code, 404)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("stalls:list")), "Closed Stall")

    def test_search_stalls(self):
        self.client.force_login(self.buyer)
        r = self.client.get(reverse("stalls:list"), {"q": "santa fe"})
        self.assertContains(r, "Vic&#x27;s Crabs")
        r = self.client.get(reverse("stalls:list"), {"q": "zzz"})
        self.assertContains(r, "No stalls match")

    def test_my_stalls_vendor_only_and_own_only(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("stalls:mine")).status_code, 302)
        self.client.force_login(self.vendor2)
        self.assertNotContains(self.client.get(reverse("stalls:mine")), "Vic&#x27;s Crabs")

    def test_dashboards_show_stalls(self):
        self.client.force_login(self.buyer)
        self.assertContains(self.client.get(reverse("accounts:buyer_dashboard")), "Featured stalls")
        self.client.force_login(self.vendor)
        self.assertContains(self.client.get(reverse("accounts:vendor_dashboard")), "Vic&#x27;s Crabs")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("accounts:admin_dashboard")), "stalls (")
