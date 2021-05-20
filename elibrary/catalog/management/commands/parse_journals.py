from django.core.management.base import BaseCommand, CommandError
import glob, os

from catalog.models import *
import xmlparser
import xml.etree.ElementTree as ET

from django.db.utils import IntegrityError
from django.db import transaction

from loguru import logger
from sys import stdout

from helpres import find_and_get, get_plain_text

import datetime

class Command(BaseCommand):
    help = "Parses xml and fill db with data"

    @logger.catch
    def handle(self, *args, **options):

        logger.remove()
        logger.add(stdout,  colorize=True, format="<green>INFO:</green> | <yellow>{message}</yellow>", level="INFO")

        JOURNALS_ROOT = os.environ.get("JOURNALS_ROOT")
        DUMPS_ROOT = os.environ.get("DUMPS_ROOT")
        
        SQL_DATABASE = os.environ.get("SQL_DATABASE")
        SQL_USER = os.environ.get("SQL_USER")
        SQL_PASSWORD = os.environ.get("SQL_PASSWORD")
        SQL_HOST = os.environ.get("SQL_HOST")
        SQL_PORT = os.environ.get("SQL_PORT")

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        dump_fullname = f"{DUMPS_ROOT}/{now}.sql"

        os.system(f"mysqldump -y -h {SQL_HOST} -u {SQL_USER} --password={SQL_PASSWORD} {SQL_DATABASE} > {dump_fullname}")

        os.chdir(JOURNALS_ROOT)
        logger.info("Parsing started:")
        for k, file in enumerate(glob.glob("*.xml")):
            _parse(file)
            logger.info(str(k+1) + " - xml is parsed.")


@transaction.atomic
def _parse(file):

    print("\n")
    logger.info(f"{file} is parsing...")

    try:
        tree = ET.parse(file)
    except ET.ParseError:
        logger.info("Xml file - %s - is not valid" % file)
        return

    try:
        journal_parser = JournalParser(tree.getroot(), elibId="titleid", rus_title="journalInfo/title")
    except JournalParser.NoElibId as exc:
        logger.info(exc)
        return
    except JournalParser.NotValidElibId as exc:
        logger.info(exc)
        return
    else:
        journal_parser.get_or_create()

    try:
        issue_tag = journal_parser.tag.find("issue")
    except:
        pass


    issue_parser = IssueParser(root=issue_tag,
                                  dateUni="dateUni", volume="volume", number="number",
                                  journal=journal_parser.get_model())

    issue_parser.get_or_create()

    articles_tag = issue_tag.find("articles")  # articles tag

    rus_section = None
    eng_section = None

    if articles_tag is not None:

        for child_tag in articles_tag:

            if child_tag.tag == "section":
                rus_section = find_and_get(child_tag, "secTitle[@lang='RUS']")
                eng_section = find_and_get(child_tag, "secTitle[@lang='ENG']")
            elif child_tag.tag == "article":

                try:
                    article_parser = ArticleParser(root=child_tag,
                                                    rus_title="artTitles/artTitle[@lang='RUS']",
                                                    eng_title="artTitles/artTitle[@lang='ENG']",
                                                    rus_annotation="abstracts/abstract[@lang='RUS']",
                                                    eng_annotation="abstracts/abstract[@lang='ENG']",
                                                    furl="files/furl", pdf_name="files/file",
                                                      langPubl="langPubl", artType="artType",
                                                      rus_section=rus_section, eng_section=eng_section,
                                                      issue=issue_parser.get_model(), journal=journal_parser.get_model())
                except ArticleParser.ArticleDoesNotHavePdfFile as exc:
                    continue
                else:
                    article_parser.save()

                keywords_tag = child_tag.find("keywords")

                if keywords_tag is not None:
                    for kwdgroup_tag in keywords_tag:
                        lang = kwdgroup_tag.attrib['lang']
                        for keyword_tag in kwdgroup_tag:
                            keyword_parser = KeywordParser(root=keyword_tag, lang=lang,
                                                           formated_word="", article=article_parser.get_model())
                            keyword_parser.save()

                artAuthors_tag = child_tag.find("authors")

                if artAuthors_tag is not None:

                    for a in artAuthors_tag:
                        author_parser = AuthorParser(a, num=("", "num"),
                                        rus_surname="individInfo[@lang='RUS']/surname",
                                        eng_surname="individInfo[@lang='ENG']/surname",
                                        rus_initials="individInfo[@lang='RUS']/initials",
                                        eng_initials="individInfo[@lang='ENG']/initials",
                                        rus_affilation="individInfo[@lang='RUS']/orgName",
                                        eng_affilation="individInfo[@lang='ENG']/orgName",
                                        article=article_parser.get_model())

                        author_parser.save()

                references_tag = child_tag.find("references")

                if references_tag is not None:
                    for ref_tag in references_tag:
                        for refInfo_tag in ref_tag:
                            reference_parser = ReferenceParser(root=refInfo_tag, lang=("", "lang"),
                                                               refInfo="text", article=article_parser.get_model())
                            reference_parser.save()


# PARSERS -------------------------------------------------------------------

class JournalParser(xmlparser.AbstractDjangoParser):

    model_params = {'elibId', 'rus_title'}
    Model = Journal

    class NoElibId(TypeError):
        pass

    class NotValidElibId(ValueError):
        pass

    @staticmethod
    def elibId_from(elibId, rus_title):
        DAN_ELIB_ID = 7781
        # Sometimes different xml of DAN can have different elibId(titleId)
        if rus_title == "Доклады академии наук" or rus_title == "ДОКЛАДЫ АКАДЕМИИ НАУК" or \
                rus_title == "ДКЛАДЫ АКАДЕМИИ НАУК" \
                or rus_title == "ДОКЛАДЫ AKAДЕМИИ HAУK":  # here "AKA" in latin
            return DAN_ELIB_ID

        bad_to_good_elibId = {}
        if elibId in bad_to_good_elibId:
            return bad_to_good_elibId[int(elibId)]

        return elibId

    @staticmethod
    def validate_elibId(elibId):
        if elibId is None:
            raise JournalParser.NoElibId("Xml does not contain elibrary journal id")

        VALID_ELIB_IDS = {7781, 25478, 25479, 53145, 7806, 7920, 7981, 8297, 7798, 7802, 7853}
        if int(elibId) not in VALID_ELIB_IDS:
            raise JournalParser.NotValidElibId("Not valid elibrary journal id")

    def get_or_create(self):
        self.model = self.Model.objects.get_or_create(elibId=self._get_model_param("elibId"),
                                                      defaults={'rus_title': self._get_model_param("rus_title")})[0]


class IssueParser(xmlparser.AbstractDjangoParser):

    Model = Issue
    model_params = {"dateUni", "volume", "number", "journal"}
    external_data = {"journal"}

    class IssueNotUnique(ValueError):
        pass

    @staticmethod
    def number_handler(number):
        if number == "З":
            return 3
        return number

    def save(self):

        self.model = self.Model(**self.instance_model_params)
        try:
            self.model.save()
        except IntegrityError as exc:
            raise IssueParser.IssueNotUnique(
                "There is already issue with dateUni - {dateUni}, volume - {volume}, number - {number} in db".
                format(dateUni=self.model.dateUni, volume=self.model.volume, number=self.model.number))

    # use get_or_create if you want to add new info in an issue or edit old articles
    def get_or_create(self):
        self.model = self.Model.objects.get_or_create(journal=self._get_model_param("journal"),
                                                      dateUni=self._get_model_param("dateUni"),
                                                      volume=self._get_model_param("volume"),
                                                      number=self._get_model_param("number"),
                                                      )[0]

class ArticleParser(xmlparser.AbstractDjangoParser):

    Model = Article
    external_data = {"journal", "issue", "rus_section", "eng_section"}
    data = {"rus_section", "eng_section",
                 "artType", "langPubl", "rus_title", "eng_title",
                 "rus_annotation", "eng_annotation", "furl", "pdf_name",
                 "journal", "issue"}

    model_params = {"rus_section", "eng_section",
                 "artType", "langPubl", "rus_title", "eng_title",
                 "rus_annotation", "eng_annotation", "furl", "pdf_name", "pdf",
                 "issue"}

    class ArticleDoesNotHavePdfFile(Exception):
        pass

    @staticmethod
    def rus_title_handler(rus_title):
        return get_plain_text(rus_title) if rus_title is not None else None

    @staticmethod
    def eng_title_handler(eng_title):
        return get_plain_text(eng_title) if eng_title is not None else None

    @staticmethod
    def pdf_name_handler(pdf_name):
        if pdf_name is None:
            raise ArticleParser.ArticleDoesNotHavePdfFile("There is no information about pdf file of this article in the xml")
        return pdf_name

    @staticmethod
    def pdf_from(pdf_name, issue, journal):
        return "journals/" + str(journal.pk) + "_journal/" + "issues/" + \
               "%s_%s_%s/" % (issue.dateUni, issue.volume, issue.number) + pdf_name

    def save(self):

        self.model = self.Model(**self.instance_model_params)

        old_articles = self.Model.objects.filter(rus_title__iexact=self._get_model_param("rus_title"))
        if len(old_articles) > 1:
            print(f"\n\n WARNING! {len(old_articles)} articles were detected with the same rus_title \n\n")
        if len(old_articles) > 2:
            self.model = old_articles[1]
        else:
            for a in old_articles:
                a.references.all().delete()
                a.authors.all().delete()
            old_articles.delete()
            self.model.save()


class AuthorParser(xmlparser.AbstractDjangoParser):

    Model = Author

    data = {"rus_surname", "eng_surname",
                 "rus_initials", "eng_initials",
                "rus_affilation", "eng_affilation",
                "num", "article"}

    model_params = {"rus_surname", "eng_surname",
                "rus_initials", "eng_initials",
                "rus_affilation", "eng_affilation",
                "num", "article"}

    external_data = {"article"}
    internal_attr_data = {"num"}


class ReferenceParser(xmlparser.AbstractDjangoParser):

    Model = Reference
    external_data = {"article"}
    internal_attr_data = {"lang"}


class KeywordParser(xmlparser.AbstractDjangoParser):

    Model = Keyword
    external_data = {"article", "lang"}
    data = {"article", "lang", "formated_word"}

    @staticmethod
    def word_from(formated_word):
        return get_plain_text(formated_word) if formated_word is not None else None

    def save(self):
        self.model = self.Model.objects.get_or_create(
            word=self._get_model_param("word"),
            defaults={'lang': self._get_model_param("lang"),
                      'formated_word': self._get_model_param("formated_word")})[0]

        self.model.articles.add(self._get_raw_data("article"))
        self.model.save()

# -----------------------------------------------------------------------------