from django import forms

from .models import MESSAGE_MAX_LENGTH, Kind


class FeedbackForm(forms.Form):
    # Field names/ids like "feedback-message": the dialog sits on every page, next to
    # other forms (the workout's), and must never clash with them.
    prefix = "feedback"

    kind = forms.ChoiceField(
        label="Rodzaj",
        choices=Kind.choices,
        initial=Kind.BUG,
        widget=forms.RadioSelect(attrs={"class": "feedback-kind"}),
        error_messages={
            "invalid_choice": "Wybierz rodzaj zgłoszenia.",
            "required": "Wybierz rodzaj zgłoszenia.",
        },
    )
    message = forms.CharField(
        label="Opisz, co się wydarzyło albo co proponujesz",
        max_length=MESSAGE_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": MESSAGE_MAX_LENGTH}),
        error_messages={
            "required": "Napisz kilka słów: co się stało albo co proponujesz.",
            "max_length": f"Maksymalnie {MESSAGE_MAX_LENGTH} znaków.",
        },
    )
    # The page the report is about; HTMX also sends it in the HX-Current-URL header.
    page = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if not message:
            raise forms.ValidationError("Napisz kilka słów: co się stało albo co proponujesz.")
        return message
