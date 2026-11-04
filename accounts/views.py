from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SignUpForm, UserSettingsForm
from .services import get_user_settings


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def settings_view(request):
    # No id in the URL: the page always edits the logged-in user's own settings.
    form = UserSettingsForm(request.POST or None, instance=get_user_settings(request.user))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Settings saved.")
        return redirect("settings")
    return render(request, "accounts/settings.html", {"form": form})
