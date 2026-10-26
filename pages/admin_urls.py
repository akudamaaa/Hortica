from django.urls import path
from .views import AdminLogoutView, admin_dashboard

urlpatterns = [
    path("", admin_dashboard, name="admin-dashboard"),
    path("logout/", AdminLogoutView.as_view(), name="admin-logout"),
]
