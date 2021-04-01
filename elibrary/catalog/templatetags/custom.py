from django import template

register = template.Library()

from ..models import *


@register.simple_tag(takes_context=True)
def translate(context, rus_version, eng_version):
    return eng_version if context["lang"] == "ENG" else rus_version


@register.simple_tag(takes_context=True)
def default_translate(context, rus_version, eng_version, rus_default="", eng_default="", total_fail_default=""):
    if context["lang"] == "ENG":
        if eng_version is None:
            return total_fail_default if eng_default is None else eng_default
        else:
            return eng_version
    else:
        if rus_version is None:
            return total_fail_default if rus_default is None else rus_default
        else:
            return rus_version
