"""Business logic for accounts and user settings."""

from urllib.parse import quote, urlencode

from django.conf import settings

from .models import UserSettings


def get_user_settings(user):
    """The user's settings, created with defaults the first time they are needed."""
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    return user_settings


def is_supported_language(language):
    return language in dict(settings.LANGUAGES)


def account_language(user):
    """The language saved on the account ("pl" / "en"), or "" if none was chosen.

    Read on every request by config.middleware.UserLanguageMiddleware, so it is one
    small query, remembered on the user object, and it never creates a settings row.
    """
    if not user.is_authenticated:
        return ""
    if not hasattr(user, "_account_language"):
        language = UserSettings.objects.filter(user=user).values_list("language", flat=True).first()
        user._account_language = language if is_supported_language(language) else ""
    return user._account_language


def save_account_language(user, language):
    user_settings = get_user_settings(user)
    if user_settings.language != language:
        user_settings.language = language
        user_settings.save(update_fields=["language"])
    user._account_language = language


def set_language_cookie(response, language):
    """The same cookie Django's set_language view sets (name, age, flags from settings)."""
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )


def ios_shortcut_url(shortcut_name, seconds, return_url):
    """URL that runs an iOS shortcut with the rest length as input, then comes back.

    shortcuts://x-callback-url/run-shortcut is Apple's documented URL scheme:
    `input=text&text=90` hands "90" to the shortcut as Shortcut Input, and
    `x-success` is opened when the shortcut finishes, which returns to LiftLog.
    Every value is percent-encoded (including ":" and "/" inside x-success).
    """
    params = {
        "name": shortcut_name,
        "input": "text",
        "text": str(int(seconds)),
        "x-success": return_url,
    }
    return "shortcuts://x-callback-url/run-shortcut?" + urlencode(params, quote_via=quote)
