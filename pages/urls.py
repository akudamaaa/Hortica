from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("history/", views.history, name="history"),
    path("crew/", views.crew, name="crew"),
    path("voyages/", views.voyages, name="voyages"),
    path("archive/", views.archive, name="archive"),
    path("registration/", views.registration, name="registration"),
]
