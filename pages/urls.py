from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("index.htm", views.home, name="legacy-home"),
    path("project.htm", views.project, name="project"),
    path("project/", views.project, name="project-modern"),
    path("history.htm", views.history, name="history"),
    path("history/", views.history, name="history-modern"),
    path("crew.htm", views.crew, name="crew"),
    path("crew/", views.crew, name="crew-modern"),
    path("track.htm", views.voyages, name="voyages"),
    path("voyages/", views.voyages, name="voyages-modern"),
    path("koord.htm", views.coordinates, name="coordinates"),
    path("coordinates/", views.coordinates, name="coordinates-modern"),
    path("oldspice.htm", views.oldspice, name="oldspice"),
    path("2006.htm", views.voyage_2006, name="voyage-2006"),
    path("2007.htm", views.voyage_2007, name="voyage-2007"),
    path("2009.htm", views.voyage_2009, name="voyage-2009"),
    path("2010.htm", views.voyage_2010, name="voyage-2010"),
    path("archive/", views.photo_archive, name="archive"),
    path("registration/", views.registration, name="registration"),
]
