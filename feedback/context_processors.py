from .forms import FeedbackForm


def feedback_form(request):
    """An empty "Zgłoś" form for the dialog in base.html (logged-in users only)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    return {"feedback_form": FeedbackForm(initial={"page": request.get_full_path()})}
