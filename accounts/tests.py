from django.test import TestCase
from django.urls import reverse

from .models import User

PW = "Tide&Salt2026"


class AccountTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("buyer@x.com", PW, full_name="Bea Buyer", role="BUYER")
        self.vendor = User.objects.create_user("vendor@x.com", PW, full_name="Vic Vendor", role="VENDOR")
        self.admin = User.objects.create_superuser("admin@x.com", PW, full_name="Ann Admin")

    def reg(self, **over):
        data = {"full_name": "New Person", "email": "new@x.com", "contact_number": "", "role": "BUYER",
                "password1": PW, "password2": PW}
        data.update(over)
        return self.client.post(reverse("accounts:register"), data)

    # Registration
    def test_register_success_hashes_password(self):
        r = self.reg()
        self.assertRedirects(r, reverse("accounts:login"))
        u = User.objects.get(email="new@x.com")
        self.assertNotEqual(u.password, PW)
        self.assertTrue(u.check_password(PW))

    def test_register_duplicate_email_case_insensitive(self):
        self.assertContains(self.reg(email="BUYER@x.com"), "already exists")

    def test_register_password_mismatch(self):
        r = self.reg(password2="Different123!")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(email="new@x.com").exists())

    def test_register_invalid_email(self):
        self.assertEqual(self.reg(email="not-an-email").status_code, 200)
        self.assertFalse(User.objects.filter(email="not-an-email").exists())

    def test_cannot_register_as_admin(self):
        self.assertEqual(self.reg(role="ADMIN").status_code, 200)
        self.assertFalse(User.objects.filter(email="new@x.com").exists())

    # Login / logout
    def test_login_invalid(self):
        r = self.client.post(reverse("accounts:login"), {"username": "buyer@x.com", "password": "bad"})
        self.assertContains(r, "Incorrect email or password")

    def test_login_redirects_by_role(self):
        for user, url in [(self.buyer, "buyer_dashboard"), (self.vendor, "vendor_dashboard"), (self.admin, "admin_dashboard")]:
            self.client.logout()
            r = self.client.post(reverse("accounts:login"), {"username": user.email, "password": PW}, follow=True)
            self.assertEqual(r.redirect_chain[-1][0], reverse(f"accounts:{url}"))

    def test_logout_ends_session(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("accounts:logout"))
        r = self.client.get(reverse("accounts:profile"))
        self.assertEqual(r.status_code, 302)

    def test_logged_out_redirected_to_login(self):
        for name in ["dashboard", "buyer_dashboard", "vendor_dashboard", "admin_dashboard", "profile", "profile_edit"]:
            r = self.client.get(reverse(f"accounts:{name}"))
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("accounts:login"), r.url)

    # Role protection
    def test_wrong_role_cannot_open_other_dashboards(self):
        self.client.force_login(self.buyer)
        for name in ["vendor_dashboard", "admin_dashboard"]:
            r = self.client.get(reverse(f"accounts:{name}"))
            self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("accounts:buyer_dashboard")).status_code, 200)

    # Profile
    def test_profile_update(self):
        self.client.force_login(self.buyer)
        self.client.post(reverse("accounts:profile_edit"),
                         {"full_name": "Bea Updated", "email": "buyer@x.com", "contact_number": "09171234567"})
        self.buyer.refresh_from_db()
        self.assertEqual(self.buyer.full_name, "Bea Updated")

    def test_profile_email_must_stay_unique(self):
        self.client.force_login(self.buyer)
        r = self.client.post(reverse("accounts:profile_edit"), {"full_name": "Bea", "email": "vendor@x.com"})
        self.assertContains(r, "Another account already uses")

    def test_profile_shows_only_own_data(self):
        self.client.force_login(self.buyer)
        r = self.client.get(reverse("accounts:profile"))
        self.assertContains(r, "buyer@x.com")
        self.assertNotContains(r, "vendor@x.com")
