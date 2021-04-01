from django.urls import path
from . import views

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("", views.index, name="index"),
    path("journal/<int:id>", views.journal_details, name="journal_details"),

    path("issue_by_year", views.issue_by_year, name="issue_by_year"),
    path("issue_by_volume", views.issue_by_volume,name="issue_by_volume"),
    path("issue_by_number", views.issue_by_number,name="issue_by_number"),

    path("event/<int:id>", views.event_details, name="event_details"),
    path("issue/<int:id>", views.issue_details, name="issue_details"),

    path("videos", views.videos, name="videos"),
    path("journals", views.journals, name="journals"),


    path("rubric_catalog", views.rubric_catalog, name="rubric_catalog"),
    path("about", views.about, name="about"),
    path("news", views.news, name="news"),
    path("rubricator", views.rubricator, name="rubricator"),

    path("switch_lang", views.switch_lang, name="switch_lang"),

    path("search", views.search, name="search"),
]