from allauth.account.models import EmailAddress
from allauth.account.views import EmailVerificationSentView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import UserSettingsForm
from .services import get_user_settings

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
        messages.info(request, "This address is already confirmed. You can log in.")
        return redirect("account_login")
    if not send_verification_email_to_address(request, address):
        messages.warning(
            request, "We sent a link a moment ago. Wait 3 minutes before asking for another."
        )
    elif not getattr(request, "confirmation_mail_failed", False):  # see AccountAdapter
        messages.success(request, "Sent! Check your inbox (and the spam folder).")
    return redirect("account_email_verification_sent")


@login_required
def settings_view(request):
    # No id in the URL: the page always edits the logged-in user's own settings.
    form = UserSettingsForm(request.POST or None, instance=get_user_settings(request.user))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Settings saved.")
        return redirect("settings")
    address = EmailAddress.objects.filter(user=request.user, primary=True).first()
    return render(request, "accounts/settings.html", {"form": form, "email_address": address})
