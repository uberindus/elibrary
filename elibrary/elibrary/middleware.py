class SetLanguageMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        lang = request.session.get("lang", None)
        if lang is None:
            request.session["lang"] = "RUS" if request.LANGUAGE_CODE == "ru" else "ENG"

        return self._get_response(request)
