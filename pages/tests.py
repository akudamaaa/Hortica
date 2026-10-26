from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .views import legacy_pages


class PublicPagesTests(TestCase):
    def test_all_source_pages_and_additions_render(self):
        for name in (
            "home", "project", "history", "crew", "voyages", "coordinates", "oldspice",
            "voyage-2006", "voyage-2007", "voyage-2009", "voyage-2010", "registration",
        ):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_original_voyage_list_keeps_all_route_rows(self):
        response = self.client.get(reverse("voyages"))
        self.assertContains(response, "32 записей")
        self.assertContains(response, "1984")
        self.assertContains(response, "2009047sm.jpg")

    def test_story_photo_stays_in_article_order(self):
        response = self.client.get(reverse("voyage-2006"))
        self.assertContains(response, 'class="source-photo"')
        self.assertContains(response, "2006001sm.jpg")
        self.assertContains(response, "2006001.jpg")
        source_caption = next(image["caption"] for image in legacy_pages()["2006"]["images"] if image["caption"])
        self.assertContains(response, source_caption)

    def test_crew_members_have_separate_cards_and_matching_portraits(self):
        response = self.client.get(reverse("crew"))
        self.assertContains(response, 'class="crew-card"')
        self.assertContains(response, "Трекало Михаил Юрьевич")
        self.assertContains(response, "Моисеев Денис")
        self.assertContains(response, "/static/legacy/kaptan.jpg")
        self.assertContains(response, "/static/legacy/ya.jpg")
        self.assertContains(response, "/static/legacy/oldgavr.jpg")

    def test_project_uses_confirmed_1960_date_without_developer_note(self):
        response = self.client.get(reverse("project"))
        self.assertContains(response, "в 1960 году и в том же году совершила первый поход")
        self.assertNotContains(response, "Подтверждённая дата")

    def test_old_archive_alias_opens_complete_photo_archive(self):
        response = self.client.get(reverse("archive"))
        self.assertRedirects(response, f"{reverse('voyages')}#photo-archive", fetch_redirect_response=False)

    def test_photo_archive_collects_all_source_images(self):
        response = self.client.get(reverse("voyages"))
        self.assertContains(response, 'id="photo-archive"')
        self.assertContains(response, "Фотоархив")
        self.assertContains(response, "295 снимков")
        self.assertContains(response, "old001sm.jpg")

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
        self.assertContains(response, "Приём заявок временно закрыт")
        self.assertContains(response, "не отправляются")
        self.assertContains(response, "disabled")
