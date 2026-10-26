from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy


def home(request):
    return render(request, "pages/home.html")


def history(request):
    return render(request, "pages/history.html")


def crew(request):
    return render(request, "pages/crew.html")


def voyages(request):
    return render(request, "pages/voyages.html")


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
