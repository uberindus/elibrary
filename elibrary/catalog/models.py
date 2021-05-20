from django.db import models
from django.db.models import Q

from django.urls import reverse
from itertools import groupby

import re


def journal_rus_cover_path(journal, filename):
    extension = filename.split(".")[-1]
    return f"journals/{journal.pk}_journal/rus_relevant_cover.{extension}"


def journal_eng_cover_path(instance, filename):
    extension = filename.split(".")[-1]
    return f"journals/{journal.pk}_journal/eng_relevant_cover.{extension}"


class Journal(models.Model):

    elibId = models.PositiveIntegerField(blank=True, null=True, unique=True)

    rus_title = models.CharField(max_length=256,)
    eng_title = models.CharField(max_length=256, blank=True,)

    rus_description = models.TextField(blank=True, null=True)
    eng_description = models.TextField(blank=True, null=True)

    sdi = models.CharField(blank=True, max_length=32, null=True)

    rus_relevant_cover = models.FileField(blank=True, null=True, upload_to=journal_rus_cover_path)
    eng_relevant_cover = models.FileField(blank=True, null=True, upload_to=journal_eng_cover_path)

    catalog_num = models.PositiveSmallIntegerField(null=True, blank=True)

    def issues_grouped_by_year(self):
        grouped_data = groupby(self.issues.order_by('dateUni', 'volume', 'number'), key=lambda x: x.dateUni)
        years_groups = [(k, list(g)) for k, g in grouped_data]
        return years_groups

    def __str__(self):
        return self.rus_title if self.rus_title is not None else self.pk

    def get_url(self):
        return reverse('journal_details', kwargs={'id': self.pk})

    def last_pub(self, lang="RUS"):
        if lang == "RUS":
            last_pub = self.publications.filter(pub_lang="RUS")
        else:
            last_pub = self.publications.filter(pub_lang="ENG")
        return last_pub.order_by("-year").first()

    class Meta:
        ordering = ['catalog_num', ]


def publication_cover_path(pub, filename):
    extension = filename.split(".")[-1]
    return f"journals/{pub.journal.pk}_journal/publications_covers/{pub.pk}.{extension}"


class Publication(models.Model):

    journal = models.ForeignKey(Journal, blank=True, null=True, on_delete=models.SET_NULL, related_name="publications")

    pub_lang = models.CharField(max_length=3, choices=[('RUS', 'russian'), ('ENG', 'english')], null=True)

    year = models.PositiveSmallIntegerField(null=True)

    issn_print = models.CharField(blank=True, max_length=32, null=True)
    issn_online = models.CharField(blank=True, max_length=32, null=True)

    rus_org_title = models.CharField(max_length=255, blank=True)
    eng_org_title = models.CharField(max_length=255, blank=True, )

    site_url = models.URLField(blank=True)

    date_foundation = models.PositiveSmallIntegerField(blank=True, null=True, )

    rus_main_editor = models.CharField(blank=True, max_length=255,)
    eng_main_editor = models.CharField(blank=True, max_length=255,)

    rinc_impact_factor = models.CharField(max_length=64, blank=True, null=True)

    isi_impact_factor = models.CharField(max_length=64, blank=True, null=True)
    scimago_journal_rank = models.CharField(max_length=64, blank=True, null=True)

    pereodicity = models.PositiveSmallIntegerField(blank=True, null=True)
    pereodicity_clarification = models.CharField(blank=True, null=True, max_length=256)

    cover = models.FileField(blank=True, null=True, upload_to=publication_cover_path)

    def __str__(self):
        s = self.journal.rus_title + " " if self.journal.rus_title is not None else ""
        return s + self.pub_lang + " " + str(self.year)


class JournalIndexingRefering(models.Model):
    publisher = models.ForeignKey(Publication, blank=True, null=True, on_delete=models.SET_NULL,
                                related_name="indexing_orgs")
    org_title = models.CharField(max_length=256, blank=True, null=True)


class Issue(models.Model):
    pages = models.CharField(max_length=64, blank=True, null=True)
    dateUni = models.PositiveSmallIntegerField(blank=True, null=True)
    volume = models.PositiveSmallIntegerField(blank=True, null=True)
    number = models.PositiveSmallIntegerField(blank=True, null=True)
    journal = models.ForeignKey(Journal, null=True, on_delete=models.SET_NULL, related_name="issues")


    def get_url(self):
        return reverse('issue_details', kwargs={'id': self.pk})

    def __str__(self):
        return "journal - %s | dateUni - %s, volume - %s, number - %s" % (self.journal.rus_title, self.dateUni, self.volume, self.number)

    class Meta:
        ordering = ['dateUni', 'volume', 'number']
        unique_together = ('journal', 'dateUni', 'volume', "number")



class Keyword(models.Model):

    word = models.CharField(max_length=255, unique=True)
    lang = models.CharField(max_length=3, blank=True, choices=[('RUS', 'russian'), ('ENG', 'english'), ('ANY', 'anylang')])
    formated_word = models.CharField(max_length=1024, blank=True)

    def __str__(self):
        return self.word


def article_pdf_path(article, filename):
    if article.pdf_name is not None:
        filename = article.pdf_name
    return f"journals/{article.issue.journal.pk}_journal/issues/{article.issue.dateUni}_{article.issue.volume}_{article.issue.number}/{filename}"

class Article(models.Model):

    rus_section = models.CharField(max_length=512, blank=True, null=True)
    eng_section = models.CharField(max_length=512, blank=True, null=True)
    artType = models.CharField(max_length=8, blank=True, null=True)
    langPubl = models.CharField(max_length=3, choices=[('RUS', 'russian'), ('ENG', 'english')], blank=True, null=True)
    rus_title = models.CharField(max_length=2048, blank=True, null=True)
    eng_title = models.CharField(max_length=2048, blank=True, null=True)
    rus_annotation = models.TextField(blank=True, null=True)
    eng_annotation = models.TextField(blank=True, null=True)
    furl = models.URLField(blank=True, null=True)
    pdf = models.FileField(blank=True, null=True, upload_to=article_pdf_path)
    pdf_name = models.CharField(max_length=512, blank=True, null=True)
    issue = models.ForeignKey(Issue, blank=True, null=True, on_delete=models.SET_NULL, related_name="articles", )
    keywords = models.ManyToManyField(Keyword, blank=True, related_name="articles", null=True)

    def __str__(self):
        if self.rus_title is not None:
            return self.rus_title
        elif self.eng_title is not None:
            return self.eng_title
        else:
            return str(self.pk)


class Reference(models.Model):
    refInfo = models.CharField(max_length=4096, null=True)
    lang = models.CharField(max_length=3, choices=[('RUS', 'russian'), ('ENG', 'english'), ('ANY', 'anylang')], blank=True, null=True)
    article = models.ForeignKey(Article,  null=True, on_delete=models.SET_NULL, related_name="references")

    def __str__(self):
        return self.refInfo


class Video(models.Model):

    langPubl = models.CharField(max_length=3, choices=[('RUS', 'russian'), ('ENG', 'english')], blank=True, null=True)

    rus_title = models.CharField(max_length=4096, null=True)
    eng_title = models.CharField(max_length=4096, null=True)

    rus_description = models.TextField(blank=True, null=True)
    eng_description = models.TextField(blank=True, null=True)

    date = models.DateField(blank=True, null=True)

    youtube_url = models.URLField(blank=True, null=True)

    youtube_embedding_url = models.URLField(blank=True, null=True)

    def __str__(self):
        if self.rus_title is not None:
            return self.rus_title
        elif self.eng_title is not None:
            return self.eng_title
        else:
            return str(self.pk)

    def get_rus_date(self):
        MONTHS_DICT = {1: "Янв", 2: "Фев", 3: "Мар", 4: "Апр", 5: "Май", 6: "Июн", 7: "Июл", 8: "Авг", 9: "Сен",
                       10: "Окт", 11: "Ноя", 12: "Дек"}
        n_month = int(self.date.strftime("%m"))
        return MONTHS_DICT[n_month] + ". " + self.date.strftime("%d, %Y")

    def get_eng_date(self):
        return self.date


class ScienceEvent(models.Model):
    rus_title = models.CharField(max_length=256, blank=True, null=True)
    eng_title = models.CharField(max_length=256, blank=True, null=True)

    year = models.PositiveSmallIntegerField(blank=True, null=True)

    header = models.FileField()

    def get_url(self):
        return reverse('event_details', kwargs={'id': self.pk})

    def __str__(self):
        return self.rus_title



class Rubric(models.Model):
    name = models.CharField(max_length=10, choices=[('chm', 'chemistry'), ('blg', 'biology'), ('phl', 'physiology')],
                            blank=True, unique=True, null=True)
    journals = models.ManyToManyField(Journal, blank=True, related_name="rubrics", null=True)
    publications = models.ManyToManyField(Publication, blank=True, related_name="rubrics", null=True)
    articles = models.ManyToManyField(Article, blank=True, related_name="rubrics", null=True)
    videos = models.ManyToManyField(Video, blank=True, related_name="rubrics", null=True)

    def __str__(self):
        return self.name


class Report(models.Model):

    scienceEvent = models.ForeignKey(ScienceEvent, on_delete=models.SET_NULL, blank=True, null=True, related_name="reports")

    rubric = models.ForeignKey(Rubric, on_delete=models.SET_NULL, blank=True, null=True)

    rus_title = models.CharField(max_length=512, blank=True, null=True)
    eng_title = models.CharField(max_length=512, blank=True, null=True)

    langPubl = models.CharField(max_length=8, blank=True, null=True)

    pdf = models.FileField(blank=True, null=True, upload_to="")

    rus_text = models.TextField(blank=True, null=True)
    eng_text = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.rus_title is not None:
            return self.rus_title
        elif self.eng_title is not None:
            return self.eng_title
        else:
            return str(self.pk)


class Author(models.Model):

    num = models.SmallIntegerField(blank=True, null=True)
    rus_surname = models.CharField(max_length=128, null=True, blank=True,)
    eng_surname = models.CharField(max_length=128, null=True, blank=True,)
    eng_initials = models.CharField(max_length=128, null=True, blank=True,)
    rus_initials = models.CharField(max_length=128, null=True, blank=True,)
    rus_affilation = models.CharField(max_length=1024, null=True, blank=True,)
    eng_affilation = models.CharField(max_length=1024, null=True, blank=True,)
    article = models.ForeignKey(Article, null=True, blank=True,  on_delete=models.SET_NULL, related_name="authors")
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.SET_NULL, related_name="authors")

    def __str__(self):
        return str(self.rus_surname) + " " + str(self.rus_initials)


    def get_article(self):
        return self.article

    def get_report(self):
        return self.report

    class Meta:
        ordering = ['num', ]