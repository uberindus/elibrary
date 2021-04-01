import re
from django.db.models import Q

from catalog.models import *
from collections import OrderedDict

# SEARCH

from django.db.models import Q

def _search_publications(search_string):
    authors_articles, authors_reports = _search_authors_pulications(search_string)

    q = Q(rus_title__icontains=search_string) | Q(eng_title__icontains=search_string)
    titles_articles = Article.objects.filter(q)
    titles_reports = Report.objects.filter(q)

    keywords_articles = Article.objects.filter(keywords__word__icontains=search_string)

    return authors_articles | titles_articles | keywords_articles, authors_reports

def _search_videos(search_string):
    return Video.objects.filter(Q(rus_title__icontains=search_string) | Q(eng_title__icontains=search_string))

def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))

def _search_authors_pulications(search_string: str):
    # Матвеева А., B,. -> Матвеева А  B
    cleared_search_string = re.sub("[,.]", " ", search_string)
    full_name_list = cleared_search_string.split()

    lang_search_string = "RUS" if has_cyrillic(cleared_search_string) else "ENG"

    if len(full_name_list) == 1:

        surname = full_name_list[0]

        if lang_search_string == "RUS":
            q = Q(authors__rus_surname__iregex=f"^{surname}")
        else:
            q = Q(authors__eng_surname__iregex=f"^{surname}")

    elif len(full_name_list) == 2:

        surname = full_name_list[0]
        name = full_name_list[1]

        if lang_search_string == "RUS":
            q = Q(authors__rus_surname__iregex=f"^{surname}", authors__rus_initials__iregex=f"^{name}.*")
        else:
            q = Q(authors__eng_surname__iregex=f"^{surname}", authors__eng_initials__iregex=f"^{name}.*")

    elif len(full_name_list) == 3:

        surname = full_name_list[0]
        name = full_name_list[1]
        patronymic = full_name_list[2]

        if lang_search_string == "RUS":
            q = Q(authors__rus_surname__iregex=surname,
                                            authors__rus_initials__iregex="^{name}\w*[\. ]?{patronymic}\w*[.]?")
        else:
            q = Q(authors__eng_surname__iregex=surname,
                                authors__eng_initials__iregex="^{name}\w*[\. ]?{patronymic}\w*[.]?")
    else:
        return Article.objects.none(), Report.objects.none()

    return Article.objects.filter(q), Report.objects.filter(q)



# FOR AJAX REQUESTS FROM JOURNAL DETAILS PAGE

def _get_issue_years_volumes_numbers_articles(journal_id):

    years = list(
        OrderedDict.fromkeys(
            (getattr(i, "dateUni") for i in Issue.objects.filter(journal__pk=journal_id).order_by("dateUni"))
        )
    )
    first_year = years[0]
    volumes, numbers, articles = _get_year_volumes_numbers_articles(journal_id, first_year)

    return years, volumes, numbers, articles


def _get_year_volumes_numbers_articles(journal_id, year):
    volumes = list(
        OrderedDict.fromkeys(
            (getattr(i, "volume") for i in Issue.objects.filter(dateUni=year, journal__pk=journal_id))
        )
    )
    numbers = _get_volume_numbers(journal_id, year, volumes[0])
    articles = _get_issue_articles(journal_id, year, volumes[0], numbers[0])
    return volumes, numbers, articles


def _get_volume_numbers_articels(journal_id, year, volume):
    numbers = _get_volume_numbers(journal_id, year, volume)
    articles = _get_issue_articles(journal_id, year, volume, numbers[0])
    return numbers, articles


def _get_number_articles(journal_id, year, volume, number):
    return _get_issue_articles(journal_id, year, volume, number)


def _get_volume_numbers(journal_id, year, volume):
    return list(
        OrderedDict.fromkeys(
            (getattr(i, "number") for i in Issue.objects.filter(dateUni=year, volume=volume, journal__pk=journal_id))
        )
    )

def _get_issue_articles(journal_id, year, volume, number):
    return Issue.objects.filter(journal__pk=journal_id, dateUni=year, volume=volume, number=number).\
        first().articles.all()
