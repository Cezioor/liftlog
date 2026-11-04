from django import forms

from exercises.models import Exercise

from .models import Plan, PlanDay, PlanExercise


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ("name",)


class PlanDayForm(forms.ModelForm):
    class Meta:
        model = PlanDay
        fields = ("name",)
        widgets = {"name": forms.TextInput(attrs={"placeholder": "e.g. Push"})}


class PlanExerciseForm(forms.ModelForm):
    class Meta:
        model = PlanExercise
        fields = ("exercise", "target_sets", "rep_min", "rep_max", "rest_seconds")
        labels = {
            "target_sets": "Sets",
            "rep_min": "Reps from",
            "rep_max": "Reps to",
            "rest_seconds": "Rest (seconds)",
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        # Only built-in exercises and the user's own ones can be picked.
        self.fields["exercise"].queryset = Exercise.objects.visible_to(user)
        for name in ("target_sets", "rep_min", "rep_max", "rest_seconds"):
            self.fields[name].widget.attrs["inputmode"] = "numeric"

    def clean(self):
        cleaned = super().clean()
        rep_min, rep_max = cleaned.get("rep_min"), cleaned.get("rep_max")
        if rep_min and rep_max and rep_min > rep_max:
            self.add_error("rep_max", "Must be at least “Reps from”.")
        return cleaned
