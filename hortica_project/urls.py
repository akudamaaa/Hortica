from django.urls import include, path

urlpatterns = [
    path("admin/login/", include("pages.admin_login_urls")),
    path("admin/", include("pages.admin_urls")),
    path("", include("pages.urls")),
]
