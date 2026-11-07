from django import forms
from django.utils.translation import gettext_lazy as _

from .models import MESSAGE_MAX_LENGTH, Kind


class FeedbackForm(forms.Form):
    # Field names/ids like "feedback-message": the dialog sits on every page, next to
    # other forms (the workout's), and must never clash with them.
    prefix = "feedback"

    kind = forms.ChoiceField(
        label=_("Kind"),
        choices=Kind.choices,
        initial=Kind.BUG,
        widget=forms.RadioSelect(attrs={"class": "feedback-kind"}),
        error_messages={
            "invalid_choice": _("Choose the kind of report."),
            "required": _("Choose the kind of report."),
        },
    )
    message = forms.CharField(
        label=_("Describe what happened or what you suggest"),
        max_length=MESSAGE_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": MESSAGE_MAX_LENGTH}),
        error_messages={
            "required": _("Write a few words: what happened or what you suggest."),
            # Django fills in %(limit_value)d when the error is raised.
            "max_length": _("At most %(limit_value)d characters."),
        },
    )
    # The page the report is about; HTMX also sends it in the HX-Current-URL header.
    page = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if not message:
            raise forms.ValidationError(_("Write a few words: what happened or what you suggest."))
        return message
