"""Business logic for accounts and user settings."""

from urllib.parse import quote, urlencode

from .models import UserSettings


def get_user_settings(user):
    """The user's settings, created with defaults the first time they are needed."""
    user_settings, _ = UserSettings.objects.get_or_create(user=user)
    return user_settings


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
