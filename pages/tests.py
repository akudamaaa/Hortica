from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class PublicPagesTests(TestCase):
    def test_public_pages_render(self):
        for name in ("home", "history", "crew", "voyages", "archive", "registration"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_photo_archive_uses_source_captions(self):
        response = self.client.get(reverse("archive"))
        self.assertContains(response, "Маяк Толбухин")
        self.assertContains(response, "2010001sm.jpg")

    def test_public_navigation_does_not_link_to_admin(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, 'href="/admin/')
        self.assertNotContains(response, "Панель управления")


class AdminAccessTests(TestCase):
    def test_admin_dashboard_requires_staff_login(self):
        response = self.client.get(reverse("admin-dashboard"))
        self.assertRedirects(response, "/admin/login/?next=/admin/")

    def test_regular_account_cannot_access_dashboard(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="visitor", password="example-only-password")
        self.client.force_login(user)
        response = self.client.get(reverse("admin-dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_staff_account_can_access_dashboard(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="staff-test",
            password="example-only-password",
            is_staff=True,
        )
        self.client.force_login(user_model.objects.get(username="staff-test"))
        response = self.client.get(reverse("admin-dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_no_public_account_creation_route_exists(self):
        response = self.client.get("/admin/register/")
        self.assertEqual(response.status_code, 404)


class RegistrationStubTests(TestCase):
    def test_registration_page_says_submission_is_disabled(self):
        response = self.client.get(reverse("registration"))
        self.assertContains(response, "данные никуда не отправляются")
        self.assertContains(response, "disabled")
