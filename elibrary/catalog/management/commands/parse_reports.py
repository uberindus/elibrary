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


        REPORTS_ROOT = os.environ.get("REPORTS_ROOT")
        DUMPS_ROOT = os.environ.get("DUMPS_ROOT")
        
        SQL_DATABASE = os.environ.get("SQL_DATABASE")
        SQL_USER = os.environ.get("SQL_USER")
        SQL_PASSWORD = os.environ.get("SQL_PASSWORD")
        SQL_HOST = os.environ.get("SQL_HOST")
        SQL_PORT = os.environ.get("SQL_PORT")

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        dump_fullname = f"{DUMPS_ROOT}/{now}.sql"
        os.system(f"mysqldump -y -h {SQL_HOST} -u {SQL_USER} --password={SQL_PASSWORD} {SQL_DATABASE} > {dump_fullname}")

        os.chdir(REPORTS_ROOT)
        logger.info("Parsing started:")
        for k, file_name in enumerate(glob.glob("*.xml")):
            _parse(file_name)
            logger.info(str(k+1) + " - xml is parsed.")


@transaction.atomic
def _parse(file):

    print("\n")
    logger.info(f"{file} is parsing...")

    tree = ET.parse(file)

    event_parser = ScienceEventParser(root=tree.getroot(), titleid="titleid", rus_title="journalInfo/title")
    event_parser.get_or_create()

    articles_tag = event_parser.tag.find("issue/articles")

    if articles_tag is not None:

        for child_tag in articles_tag:

            if child_tag.tag == "article":

                report_parser = ReportParser(root=child_tag, scienceEvent=event_parser.get_model(),
                                      langPubl="langPubl",
                                      rus_text="text[@lang='RUS']", eng_text="text[@lang='ENG']",
                                      rus_title="artTitles/artTitle[@lang='RUS']",
                                      eng_title="artTitles/artTitle[@lang='ENG']",
                                      pdf="files/file", rubric="rubrics/rubric"
                                      )
                report_parser.save()

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
                                                     report=report_parser.get_model())

                        author_parser.save()


# PARSER CLASSES

class ScienceEventParser(xmlparser.AbstractDjangoParser):

    Model = ScienceEvent
    data = {"titleid", "rus_title"}
    model_params = {"pk", "rus_title"}

    class NoPrimaryKey(TypeError):
        pass

    @staticmethod
    def validate_pk(pk):
        if pk is None:
            raise ScienceEventParser.NoPrimaryKey("Xml does not contain id of event")

    @staticmethod
    def pk_from(titleid):
        return titleid

    def get_or_create(self):
        self.model = self.Model.objects.get_or_create(pk=self._get_model_param("pk"),
                                                      defaults={'rus_title': self._get_model_param("rus_title")})[0]
        return self.model


class ReportParser(xmlparser.AbstractDjangoParser):

    Model = Report
    external_data = {"scienceEvent"}

    @staticmethod
    def rubric_handler(rubric):
        if rubric == "ХИМИЯ":
            return Rubric.objects.get_or_create(name="chm")[0]
        elif rubric == "БИОЛОГИЯ":
            return Rubric.objects.get_or_create(name="blg")[0]
        elif rubric == "ФИЗИОЛОГИЯ":
            return Rubric.objects.get_or_create(name="phl")[0]

    @staticmethod
    def rus_title_handler(rus_title):
        return get_plain_text(rus_title) if rus_title is not None else None

    @staticmethod
    def eng_title_handler(eng_title):
        return get_plain_text(eng_title) if eng_title is not None else None

    @staticmethod
    def pdf_from(pdf, scienceEvent):
        return "events/" + "%s_event/" % str(scienceEvent.pk) + "pdfs/" + pdf


class AuthorParser(xmlparser.AbstractDjangoParser):

    Model = Author

    data = {"rus_surname", "eng_surname",
                 "rus_initials", "eng_initials",
                "rus_affilation", "eng_affilation",
                "num", "report"}

    model_params = {"rus_surname", "eng_surname",
                "rus_initials", "eng_initials",
                "rus_affilation", "eng_affilation",
                "num", "report"}

    external_data = {"report"}
    internal_attr_data = {"num"}


from django.conf import settings
import helpres
from helpres import get_plain_text


if __name__ == "__main__":
    XML_DIR = "/home/" + settings.USERNAME + "/elibrary_reports_xml"

    from sys import argv
    try:
        dir = argv[1]
    except IndexError:
        dir = XML_DIR

    helpres.safe_parse(_parse, dir)








