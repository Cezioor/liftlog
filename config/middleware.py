from django.conf import settings
from django.http import HttpResponse
from django.middleware.locale import LocaleMiddleware
from django.utils import translation

from accounts.services import account_language, set_language_cookie


class HealthCheckMiddleware:
    """Answer Render's health check before any other middleware runs.

    Render may call it with the container's internal IP as the Host header, which
    ALLOWED_HOSTS would reject (400), and over plain HTTP, which SECURE_SSL_REDIRECT
    would redirect. Answering first avoids both. It doesn't touch the database,
    so a suspended Neon database can't make the service look unhealthy.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz/":
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)


class UserLanguageMiddleware(LocaleMiddleware):
    """Pick the page language: the account's language first, then Django's usual order.

    Django's LocaleMiddleware looks at the language cookie, then the browser's
    Accept-Language, then LANGUAGE_CODE (English). It doesn't know about accounts, so
    this subclass checks UserSettings.language first. On the way out it copies the
    account's language into the cookie: right after logging in on a new device the
    next page is already in that language, and after logging out it stays that way.
    """

    def process_request(self, request):
        language = account_language(request.user)
        if language:
            translation.activate(language)
            request.LANGUAGE_CODE = language
        else:
            super().process_request(request)

    def process_response(self, request, response):
        response = super().process_response(request, response)
        if settings.LANGUAGE_COOKIE_NAME in response.cookies:
            return response  # a view has just set it (language switcher, settings)
        # request.user may have changed during the request (logging in).
        language = account_language(request.user)
        if language and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != language:
            set_language_cookie(response, language)
        return response
