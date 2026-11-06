from allauth.account.forms import SignupForm as AllauthSignupForm
from django import forms
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from .models import UserSettings


class SignupForm(AllauthSignupForm):
    """allauth's sign-up form (email + password twice), plus a flag for the template."""

    @property
    def email_taken(self):
        """True when the email belongs to an existing account: the page then shows
        links to log in or reset the password."""
        return any(e.code == "email_taken" for e in self.errors.as_data().get("email", []))


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = (
            "language",
            "effort_scale",
            "ios_shortcut_enabled",
            "ios_shortcut_name",
            "keep_screen_on",
            "rest_end_sound",
        )
        widgets = {"effort_scale": forms.RadioSelect}

    # Only Polish and English, without the model's empty "not chosen" option.
    language = forms.ChoiceField(
        label=_("Language"), choices=settings.LANGUAGES, widget=forms.RadioSelect, required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional so that a form sent without it (e.g. opened before the update) still saves.
        self.fields["effort_scale"].required = False
        # Not chosen yet: show the language the page is in now.
        self.initial["language"] = self.instance.language or translation.get_language()

    def clean_language(self):
        return self.cleaned_data.get("language") or self.initial["language"]

    def clean_effort_scale(self):
        return self.cleaned_data.get("effort_scale") or self.instance.effort_scale

    def clean(self):
        cleaned = super().clean()
        cleaned["ios_shortcut_name"] = (cleaned.get("ios_shortcut_name") or "").strip()
        if cleaned.get("ios_shortcut_enabled") and not cleaned["ios_shortcut_name"]:
            self.add_error("ios_shortcut_name", _("Enter the name of your shortcut."))
        return cleaned
