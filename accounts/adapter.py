"""How django-allauth behaves in LiftLog (messages, emails)."""

import logging

from allauth.account import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

SIGNUP_DONE = _("Account created. We also sent a link to confirm your email address.")
SIGNUP_MAIL_FAILED = _(
    "Account created, but we couldn't send the link to confirm your email address. "
    "You can ask for a new one in your account settings."
)
MAIL_FAILED = _("Couldn't send the email. Try again in a few minutes.")


class AccountAdapter(DefaultAccountAdapter):
    error_messages = {
        **DefaultAccountAdapter.error_messages,
        # The sign-up page adds links to "log in" and "reset your password" under it.
        "email_taken": _("An account with this email already exists."),
    }

    def add_message(self, request, level, message_template=None, *args, **kwargs):
        # Our own messages say where the link went (see send_confirmation_mail).
        if message_template == "account/messages/email_confirmation_sent.txt":
            return
        super().add_message(request, level, message_template, *args, **kwargs)

    def send_mail(self, template_prefix, email, context):
        """Send, but never break the page if the mail service fails.

        An exception here used to surface as an error page after the account had
        already been created (the same confusing state as the double-submit bug).
        The failure is logged without the address (no personal data in logs).
        Returns True when the email went out.
        """
        try:
            super().send_mail(template_prefix, email, context)
        except Exception:
            logger.exception("Sending email %s failed", template_prefix)
            return False
        return True

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """allauth's version (link, not code), plus a message saying how it went."""
        template = (
            "account/email/email_confirmation_signup" if signup
            else "account/email/email_confirmation"
        )  # fmt: skip
        context = {
            "user": emailconfirmation.email_address.user,
            "key": emailconfirmation.key,
            "activate_url": self.get_email_confirmation_url(request, emailconfirmation),
        }
        sent = self.send_mail(template, emailconfirmation.email_address.email, context)
        if not sent:
            request.confirmation_mail_failed = True  # read by accounts.views
            messages.error(request, SIGNUP_MAIL_FAILED if signup else MAIL_FAILED)
        elif (
            signup
            and app_settings.EMAIL_VERIFICATION != app_settings.EmailVerificationMethod.MANDATORY
        ):
            # Optional verification: the user lands in the app right away, so say both
            # things at once. (Mandatory has its own "check your email" page.)
            messages.success(request, SIGNUP_DONE)
