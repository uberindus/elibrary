from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from catalog.models import *
from catalog import services

from django.core.paginator import Paginator, EmptyPage


def search(request):
    try:
        search_string = request.GET["search_string"]
    except KeyError:
        return HttpResponseRedirect(request.GET.get("next", reverse("index")))

    articles, reports = services._search_publications(search_string)
    videos = services._search_videos(search_string)

    return lang_render(request, "search.html", {"articles": articles, "reports": reports, "videos": videos})


def lang_render(request, template, context=None):
    if context is None:
        context = dict()
    context["lang"] = request.session.get("lang", "RUS")
    return render(request, template, context)


def switch_lang(request):
    request.session["lang"] = request.POST.get("lang", "RUS")
    next = request.POST["next"]

    return HttpResponseRedirect(next)


def index(request):
    return lang_render(request, "index.html")


def news(request):
    return lang_render(request, "news.html")


def about(request):
    return lang_render(request, "about.html")


def rubricator(request):
    return lang_render(request, "rubricator.html")


def journals(request):
    return lang_render(request, "journals.html", {"journals": Journal.objects.all()})


def videos(request):

    rubric_name = request.GET.get("rubric", "chm")
    videos = Video.objects.filter(rubrics__name=rubric_name)

    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1

    LIMIT = 7

    paginator = Paginator(videos, LIMIT)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(1)

    return lang_render(request, "videos.html", {
        "page": page_obj,
        "paginator": paginator,
        "rubric": rubric_name,
    })


def rubric_catalog(request):
    rubric_name = request.GET.get("rubric", "chm")
    journals = Journal.objects.filter(rubrics__name=rubric_name)
    events = ScienceEvent.objects.all()
    return lang_render(request, "rubric_catalog.html", {"journals": journals, "events": events, "rubric": rubric_name})


def event_details(request, id):
    e = get_object_or_404(ScienceEvent, pk=id)

    rubric_name = request.GET.get("rubric", "chm")
    event_reports = e.reports.filter(rubric__name=rubric_name)

    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1

    LIMIT = 15

    paginator = Paginator(event_reports, LIMIT)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(1)

    return lang_render(request, "event_details.html", {
        "event": e,
        "page": page_obj,
        "paginator": paginator,
        "rubric": rubric_name,
    })


def journal_details(request, id):
    j = get_object_or_404(Journal, pk=id)

    years, volumes, numbers, articles = services._get_issue_years_volumes_numbers_articles(id)

    last_pub = j.last_pub(lang=request.session["lang"])
    n_issues = j.issues.count()
    n_articles = sum((issue.articles.count() for issue in j.issues.all()))
    return lang_render(request, "journal_details.html", {"journal": j, "last_pub": last_pub,
                                                    "n_issues": n_issues,
                                                    "n_articles": n_articles,
                                                    "years":years,
                                                    "volumes": volumes,
                                                    "numbers":numbers,
                                                    "articles":articles})


def issue_details(request, id):
    return lang_render(request, "issue_details.html", {"issue": get_object_or_404(Issue, pk=id)})


# For AJAX requests

def issue_by_year(request):
    try:
        year = request.GET.get("year")
        journal_id = request.GET.get("journal_id")
    except KeyError:
        return Http404()
    volumes, numbers, articles = services._get_year_volumes_numbers_articles(journal_id, year)
    return JsonResponse({"articles": _articles_to_dicts(articles), "volumes": volumes, "numbers": numbers})


def issue_by_volume(request):
    try:
        year = request.GET.get("year")
        volume = request.GET.get("volume")
        journal_id = request.GET.get("journal_id")
    except KeyError:
        return Http404()

    numbers, articles = services._get_volume_numbers_articels(journal_id, year, volume)
    return JsonResponse({"articles": _articles_to_dicts(articles), "numbers": numbers})


def issue_by_number(request):
    try:
        year = request.GET.get("year")
        volume = request.GET.get("volume")
        number = request.GET.get("number")
        journal_id = request.GET.get("journal_id")
    except KeyError:
        return Http404()

    articles = services._get_number_articles(journal_id, year, volume, number)
    return JsonResponse({"articles": _articles_to_dicts(articles),})


# HELPERS

def _articles_to_dicts(articles):
    serealized = []
    for a in articles:
        article_dict = {}
        article_dict["rus_title"] = a.rus_title
        article_dict["eng_title"] = a.eng_title
        article_dict["langPubl"] = a.langPubl
        article_dict["rus_annotation"] = a.rus_annotation
        article_dict["eng_annotation"] = a.eng_annotation
        article_dict["furl"] = a.furl
        article_dict["pdf_url"] = a.pdf.url

        authors = list(a.authors.values("rus_surname", "eng_surname", "rus_initials", "eng_initials"))
        article_dict["authors"] = authors

        keywords = list(a.keywords.values("word"))
        article_dict["keywords"] = keywords

        serealized.append(article_dict)

    return serealized
