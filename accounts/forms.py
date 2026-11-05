from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, UserSettings


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Email is needed for password reset, so make it required at sign-up.
        self.fields["email"].required = True


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = (
            "effort_scale",
            "ios_shortcut_enabled",
            "ios_shortcut_name",
            "keep_screen_on",
            "rest_end_sound",
        )
        widgets = {"effort_scale": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional so that a form sent without it (e.g. opened before the update) still saves.
        self.fields["effort_scale"].required = False

    def clean_effort_scale(self):
        return self.cleaned_data.get("effort_scale") or self.instance.effort_scale

    def clean(self):
        cleaned = super().clean()
        cleaned["ios_shortcut_name"] = (cleaned.get("ios_shortcut_name") or "").strip()
        if cleaned.get("ios_shortcut_enabled") and not cleaned["ios_shortcut_name"]:
            self.add_error("ios_shortcut_name", "Enter the name of your shortcut.")
        return cleaned
