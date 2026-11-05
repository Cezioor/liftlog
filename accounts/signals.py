"""Remember which address a verification email went to, for the "check your inbox" page."""

from allauth.account.signals import email_confirmation_sent
from django.dispatch import receiver

from .views import PENDING_EMAIL_KEY


@receiver(email_confirmation_sent)
def remember_pending_email(sender, request, confirmation, signup, **kwargs):
    if request is not None and hasattr(request, "session"):
        request.session[PENDING_EMAIL_KEY] = confirmation.email_address.email
