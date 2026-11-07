from allauth.account.models import EmailAddress
from allauth.account.views import EmailVerificationSentView
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.translation import gettext as _
from django.views import i18n
from django.views.decorators.http import require_POST

from .forms import UserSettingsForm
from .services import (
    get_user_settings,
    is_supported_language,
    save_account_language,
    set_language_cookie,
)

# Set by accounts.signals whenever a verification email goes out (sign-up, or a log-in
# attempt with an address that is not confirmed yet).
PENDING_EMAIL_KEY = "pending_verification_email"


class VerificationSentView(EmailVerificationSentView):
    """'Account created! We sent a link to …' with a button to send the link again.

    Replaces allauth's page at the same URL (accounts/urls.py comes before allauth's).
    """

    template_name = "account/verification_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get(PENDING_EMAIL_KEY, "")
        return context


@require_POST
def resend_verification(request):
    """Send the confirmation link again to the address from this browser's sign-up.

    The address comes from the session, never from the form, so this can't be used to
    send mail to arbitrary addresses. allauth's rate limit allows one email per address
    every 3 minutes (ACCOUNT_RATE_LIMITS["confirm_email"]).
    """
    # Internal allauth helper (see the pin in requirements.txt): rate limit + send + message.
    from allauth.account.internal.flows.email_verification import (
        send_verification_email_to_address,
    )

    email = request.session.get(PENDING_EMAIL_KEY, "")
    address = EmailAddress.objects.filter(email__iexact=email, verified=False).first()
    if address is None:
        messages.info(request, _("This address is already confirmed. You can log in."))
        return redirect("account_login")
    if not send_verification_email_to_address(request, address):
        messages.warning(
            request, _("We sent a link a moment ago. Wait 3 minutes before asking for another.")
        )
    elif not getattr(request, "confirmation_mail_failed", False):  # see AccountAdapter
        messages.success(request, _("Sent! Check your inbox (and the spam folder)."))
    return redirect("account_email_verification_sent")


@login_required
def settings_view(request):
    # No id in the URL: the page always edits the logged-in user's own settings.
    form = UserSettingsForm(request.POST or None, instance=get_user_settings(request.user))
    if request.method == "POST" and form.is_valid():
        user_settings = form.save()
        request.user._account_language = user_settings.language  # see account_language
        # The message and the next page are already in the language just chosen.
        translation.activate(user_settings.language)
        messages.success(request, _("Settings saved."))
        response = redirect("settings")
        set_language_cookie(response, user_settings.language)
        return response
    address = EmailAddress.objects.filter(user=request.user, primary=True).first()
    return render(request, "accounts/settings.html", {"form": form, "email_address": address})


@require_POST
def set_language(request):
    """The PL · EN switcher in the footer: Django's set_language view (cookie, then back
    to `next`), plus saving the choice on the account of a logged-in user."""
    response = i18n.set_language(request)
    language = request.POST.get("language", "")
    if not is_supported_language(language):
        # Django's view accepts any language it has translations for (e.g. "de").
        response.cookies.pop(settings.LANGUAGE_COOKIE_NAME, None)
    elif request.user.is_authenticated:
        save_account_language(request.user, language)
    return response
