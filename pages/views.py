from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from pathlib import Path
from django.conf import settings
import csv


def home(request):
    return render(request, "pages/home.html")


def history(request):
    return render(request, "pages/history.html")


def crew(request):
    return render(request, "pages/crew.html")


def voyages(request):
    return render(request, "pages/voyages.html")


def archive(request):
    archive_root = Path(settings.BASE_DIR) / "assets" / "archive"
    captions_path = Path(settings.BASE_DIR) / "IMAGE-CAPTIONS.csv"
    with captions_path.open(encoding="utf-8", newline="") as captions_file:
        captions = {row["filename"]: row["description"].strip() for row in csv.DictReader(captions_file)}
    photos = []
    sections = (("voyages", "Походы"), ("history", "История"), ("crew", "Экипаж"))
    for folder, title in sections:
        for path in sorted((archive_root / folder).glob("*")):
            if path.name in {"baltica.jpg", "mast.jpg", "lefttop.jpg", "rightbottom.jpg"}:
                continue
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif"}:
                photos.append({"path": f"archive/{folder}/{path.name}", "name": path.name, "section": title, "caption": captions.get(path.name, "")})
    return render(request, "pages/archive.html", {"photos": photos})


def registration(request):
    return render(request, "pages/registration.html")


@staff_member_required(login_url=reverse_lazy("admin-login"))
def admin_dashboard(request):
    return render(request, "pages/admin_dashboard.html")


class AdminLoginView(LoginView):
    template_name = "pages/admin_login.html"
    redirect_authenticated_user = True


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy("home")
