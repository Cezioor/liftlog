"""Signal handlers: the "check your inbox" address, and the account's language."""

from allauth.account.signals import email_confirmation_sent, user_signed_up
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import translation

from .services import account_language, is_supported_language, save_account_language
from .views import PENDING_EMAIL_KEY


@receiver(email_confirmation_sent)
def remember_pending_email(sender, request, confirmation, signup, **kwargs):
    if request is not None and hasattr(request, "session"):
        request.session[PENDING_EMAIL_KEY] = confirmation.email_address.email


@receiver(user_signed_up)
def remember_signup_language(sender, request, user, **kwargs):
    """The language someone signs up in becomes the account's language, so it follows
    them to other devices."""
    language = translation.get_language()
    if is_supported_language(language):
        save_account_language(user, language)


@receiver(user_logged_in)
def use_account_language(sender, request, user, **kwargs):
    """Switch to the account's language at once, so even the "logged in" message is in it.

    The cookie is set on the way out by config.middleware.UserLanguageMiddleware.
    """
    language = account_language(user)
    if language and request is not None:
        translation.activate(language)
        request.LANGUAGE_CODE = language
