"""PD3 hardening tests for the core feature (stalls + catch updates)."""
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from stalls.models import SeafoodCategory, Stall

from .models import CatchUpdate

PW = "Tide&Salt2026"


class HardeningTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer@x.com", PW, full_name="Bea Buyer", role="BUYER")
        self.vendor = User.objects.create_user("vendor@x.com", PW, full_name="Vic Vendor", role="VENDOR")
        self.vendor2 = User.objects.create_user("vendor2@x.com", PW, full_name="Val Vendor", role="VENDOR")
        self.admin = User.objects.create_superuser("admin@x.com", PW, full_name="Ann Admin")
        self.stall = Stall.objects.create(owner=self.vendor, stall_name="Vic's Crabs", location="Santa Fe Port")
        self.other_stall = Stall.objects.create(owner=self.vendor2, stall_name="Val's Fish", location="Madridejos Pier")
        self.crab = SeafoodCategory.objects.get(name="Crab")
        self.tuna = SeafoodCategory.objects.get(name="Tuna")
        self.update = CatchUpdate.objects.create(
            stall=self.stall, category=self.crab, posted_by=self.vendor, price_per_kg="450.00"
        )
        self.other_update = CatchUpdate.objects.create(
            stall=self.other_stall, category=self.tuna, posted_by=self.vendor2, price_per_kg="300.00"
        )

    def post_catch(self, **over):
        data = {"stall": self.stall.pk, "category": self.tuna.pk, "price_per_kg": "380.50", "notes": ""}
        data.update(over)
        return self.client.post(reverse("catches:create"), data)

    # ---------- valid input
    def test_valid_catch_with_notes_is_saved_and_redirects(self):
        self.client.force_login(self.vendor)
        r = self.post_catch(notes="  about 5 kg   left ")
        self.assertRedirects(r, reverse("catches:mine"))  # redirect after POST (no double submit)
        u = CatchUpdate.objects.get(stall=self.stall, category=self.tuna)
        self.assertEqual(u.notes, "about 5 kg left")
        self.assertEqual(u.price_per_kg, Decimal("380.50"))

    def test_success_message_after_posting(self):
        self.client.force_login(self.vendor)
        r = self.client.post(reverse("catches:create"),
                             {"stall": self.stall.pk, "category": self.tuna.pk, "price_per_kg": "100"}, follow=True)
        self.assertContains(r, "posted for")

    # ---------- invalid input / business rules
    def test_same_seafood_twice_same_day_is_blocked(self):
        self.client.force_login(self.vendor)
        r = self.post_catch(category=self.crab.pk)
        self.assertContains(r, "already posted")
        self.assertEqual(CatchUpdate.objects.filter(stall=self.stall, category=self.crab).count(), 1)

    def test_editing_own_post_is_not_blocked_by_duplicate_rule(self):
        self.client.force_login(self.vendor)
        self.client.post(reverse("catches:edit", args=[self.update.pk]),
                         {"stall": self.stall.pk, "category": self.crab.pk, "price_per_kg": "470"})
        self.update.refresh_from_db()
        self.assertEqual(self.update.price_per_kg, Decimal("470.00"))

    def test_invalid_prices_are_rejected(self):
        self.client.force_login(self.vendor)
        for bad in ("0", "-1", "abc", "", "100001", "1.234"):
            r = self.post_catch(price_per_kg=bad)
            self.assertEqual(r.status_code, 200, bad)
        self.assertFalse(CatchUpdate.objects.filter(category=self.tuna, stall=self.stall).exists())

    def test_notes_too_long_is_rejected(self):
        self.client.force_login(self.vendor)
        r = self.post_catch(notes="x" * 201)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CatchUpdate.objects.filter(category=self.tuna, stall=self.stall).exists())

    def test_invalid_stall_form_values(self):
        self.client.force_login(self.vendor)
        r = self.client.post(reverse("stalls:create"), {"stall_name": "ab", "location": "x"})
        self.assertContains(r, "at least 3 characters")
        self.assertContains(r, "more specific location")

    # ---------- login required
    def test_logged_out_user_is_sent_to_login(self):
        urls = [
            reverse("catches:list"), reverse("catches:create"),
            reverse("catches:edit", args=[self.update.pk]), reverse("catches:delete", args=[self.update.pk]),
            reverse("stalls:list"), reverse("stalls:edit", args=[self.stall.pk]),
        ]
        for url in urls:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn(reverse("accounts:login"), r.url)
        r = self.client.post(reverse("catches:delete", args=[self.update.pk]))
        self.assertTrue(CatchUpdate.objects.filter(pk=self.update.pk).exists())

    # ---------- blocked access to another user's record (ID changed in URL)
    def test_vendor_cannot_open_other_vendors_records_by_id(self):
        self.client.force_login(self.vendor)
        for url in (
            reverse("catches:edit", args=[self.other_update.pk]),
            reverse("catches:delete", args=[self.other_update.pk]),
            reverse("stalls:edit", args=[self.other_stall.pk]),
            reverse("stalls:delete", args=[self.other_stall.pk]),
        ):
            self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_vendor_cannot_change_or_delete_other_vendors_records_by_post(self):
        self.client.force_login(self.vendor)
        self.client.post(reverse("catches:edit", args=[self.other_update.pk]),
                         {"stall": self.other_stall.pk, "category": self.tuna.pk, "price_per_kg": "1"})
        self.client.post(reverse("catches:delete", args=[self.other_update.pk]))
        self.client.post(reverse("stalls:delete", args=[self.other_stall.pk]))
        self.other_update.refresh_from_db()
        self.assertEqual(self.other_update.price_per_kg, Decimal("300.00"))
        self.assertTrue(Stall.objects.filter(pk=self.other_stall.pk).exists())

    def test_vendor_cannot_post_to_another_vendors_stall(self):
        self.client.force_login(self.vendor)
        r = self.post_catch(stall=self.other_stall.pk)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CatchUpdate.objects.filter(stall=self.other_stall, posted_by=self.vendor).exists())

    def test_role_checked_in_view_not_just_template(self):
        self.client.force_login(self.buyer)
        self.post_catch()
        self.client.post(reverse("stalls:create"), {"stall_name": "Buyer Stall", "location": "Some place 123"})
        self.assertEqual(CatchUpdate.objects.count(), 2)
        self.assertFalse(Stall.objects.filter(stall_name="Buyer Stall").exists())

    def test_admin_can_manage_any_record(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("catches:delete", args=[self.other_update.pk])).status_code, 200)
        self.client.post(reverse("catches:delete", args=[self.other_update.pk]))
        self.assertFalse(CatchUpdate.objects.filter(pk=self.other_update.pk).exists())

    # ---------- POST-only deletes, confirmation, safe methods
    def test_get_on_delete_only_shows_confirmation(self):
        self.client.force_login(self.vendor)
        r = self.client.get(reverse("stalls:delete", args=[self.stall.pk]))
        self.assertContains(r, "Yes, delete")
        self.assertTrue(Stall.objects.filter(pk=self.stall.pk).exists())
        r = self.client.get(reverse("catches:delete", args=[self.update.pk]))
        self.assertContains(r, "Yes, delete")
        self.assertTrue(CatchUpdate.objects.filter(pk=self.update.pk).exists())

    def test_unsupported_http_methods_are_rejected(self):
        self.client.force_login(self.vendor)
        self.assertEqual(self.client.put(reverse("catches:edit", args=[self.update.pk])).status_code, 405)
        self.assertEqual(self.client.delete(reverse("stalls:delete", args=[self.stall.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("catches:list")).status_code, 405)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)

    def test_every_post_form_has_csrf_token(self):
        self.client.force_login(self.vendor)
        for url in (reverse("catches:create"), reverse("stalls:create"),
                    reverse("catches:edit", args=[self.update.pk]), reverse("stalls:delete", args=[self.stall.pk]),
                    reverse("accounts:profile_edit")):
            self.assertContains(self.client.get(url), "csrfmiddlewaretoken", msg_prefix=url)

    # ---------- invalid URLs / IDs never crash
    def test_missing_ids_return_404(self):
        self.client.force_login(self.admin)
        for url in (reverse("stalls:detail", args=[999999]), reverse("stalls:edit", args=[999999]),
                    reverse("catches:edit", args=[999999]), reverse("catches:delete", args=[999999])):
            self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_bad_query_parameters_do_not_crash(self):
        self.client.force_login(self.buyer)
        for params in ({"page": "abc"}, {"page": "99999"}, {"category": "x"}, {"category": "99999"}, {"q": "'; DROP TABLE"}):
            self.assertEqual(self.client.get(reverse("catches:list"), params).status_code, 200, params)

    @override_settings(DEBUG=False)
    def test_custom_404_page_without_debug_info(self):
        self.client.force_login(self.buyer)
        r = self.client.get("/stalls/999999/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Page not found", status_code=404)
        self.assertNotContains(r, "Traceback", status_code=404)

    # ---------- ISS-03 pagination
    def test_search_results_are_paginated(self):
        for i in range(25):
            s = Stall.objects.create(owner=self.vendor, stall_name=f"Stall {i:02}", location="Bantayan market")
            CatchUpdate.objects.create(stall=s, category=self.crab, posted_by=self.vendor, price_per_kg=100 + i)
        self.client.force_login(self.buyer)
        r = self.client.get(reverse("catches:list"), {"category": self.crab.pk})
        self.assertContains(r, "Page 1 of 2")
        self.assertEqual(len(r.context["updates"]), 20)
        r = self.client.get(reverse("catches:list"), {"category": self.crab.pk, "page": 2})
        self.assertEqual(len(r.context["updates"]), 6)

    # ---------- data integrity
    def test_deleting_stall_removes_its_updates(self):
        self.client.force_login(self.vendor)
        self.client.post(reverse("stalls:delete", args=[self.stall.pk]))
        self.assertFalse(CatchUpdate.objects.filter(stall_id=self.stall.pk).exists())


class ProfileHardeningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("bea@x.com", PW, full_name="Bea Buyer", role="BUYER")
        self.client.force_login(self.user)

    def test_invalid_contact_number_rejected(self):
        r = self.client.post(reverse("accounts:profile_edit"),
                             {"full_name": "Bea Buyer", "email": "bea@x.com", "contact_number": "call me"})
        self.assertContains(r, "valid phone number")

    def test_non_image_photo_rejected(self):
        fake = SimpleUploadedFile("evil.txt", b"not an image", content_type="text/plain")
        r = self.client.post(reverse("accounts:profile_edit"),
                             {"full_name": "Bea Buyer", "email": "bea@x.com", "profile_photo": fake})
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_photo)

    def test_role_cannot_be_changed_through_profile_form(self):
        self.client.post(reverse("accounts:profile_edit"),
                         {"full_name": "Bea Buyer", "email": "bea@x.com", "role": "ADMIN"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "BUYER")
