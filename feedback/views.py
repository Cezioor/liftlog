from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy, ngettext

from . import services
from .forms import FeedbackForm

THANKS = gettext_lazy("Thanks! Your report has arrived.")


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


@login_required
def feedback(request):
    """The "Zgłoś" form. Usually opened in a dialog and sent with HTMX, so the page
    underneath (e.g. a workout in progress) is never reloaded; without JavaScript it is
    a normal page that redirects back afterwards."""
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid() and services.over_limit(request.user):
            form.add_error(
                None,
                ngettext(
                    "You've already sent %(count)s report in the last hour. Try again later.",
                    "You've already sent %(count)s reports in the last hour. Try again later.",
                    services.HOURLY_LIMIT,
                )
                % {"count": services.HOURLY_LIMIT},
            )
        if form.is_valid():
            page = request.headers.get("HX-Current-URL") or form.cleaned_data["page"]
            report = services.save_feedback(
                request.user,
                form.cleaned_data["kind"],
                form.cleaned_data["message"],
                page,
                request.headers.get("User-Agent", ""),
                site_url=request.build_absolute_uri("/"),
            )
            if _is_htmx(request):
                return render(request, "feedback/partials/thanks.html", {"thanks": THANKS})
            messages.success(request, THANKS)
            back = report.page
            if back and url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}):
                return redirect(back)
            return redirect("home")
    else:
        form = FeedbackForm(initial={"page": request.GET.get("page", "")})

    template = "feedback/partials/form.html" if _is_htmx(request) else "feedback/feedback_page.html"
    return render(request, template, {"feedback_form": form})
