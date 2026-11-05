from django import forms

from exercises.models import Measurement

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
    """Sets, targets and rest for one exercise in a plan day.

    The target fields depend on the exercise's measurement (Stage 1.6):
    reps from–to (weight × reps, reps), seconds from–to (time) or metres (distance + time).
    """

    TARGET_FIELDS = {
        Measurement.WEIGHT_REPS: ["rep_min", "rep_max"],
        Measurement.REPS: ["rep_min", "rep_max"],
        Measurement.TIME: ["hold_min_s", "hold_max_s"],
        Measurement.DISTANCE_TIME: ["target_distance_m"],
    }

    class Meta:
        model = PlanExercise
        # The exercise itself is chosen first in the exercise picker (see views).
        fields = (
            "target_sets",
            "rep_min",
            "rep_max",
            "hold_min_s",
            "hold_max_s",
            "target_distance_m",
            "rest_seconds",
        )
        labels = {
            "target_sets": "Sets",
            "rep_min": "Reps from",
            "rep_max": "Reps to",
            "hold_min_s": "Hold from (seconds)",
            "hold_max_s": "Hold to (seconds)",
            "target_distance_m": "Distance (metres, optional)",
            "rest_seconds": "Rest (seconds)",
        }

    def __init__(self, *args, measurement=Measurement.WEIGHT_REPS, **kwargs):
        super().__init__(*args, **kwargs)
        keep = {"target_sets", "rest_seconds", *self.TARGET_FIELDS[measurement]}
        for name in list(self.fields):
            if name not in keep:
                del self.fields[name]
        for field in self.fields.values():
            field.widget.attrs["inputmode"] = "numeric"
        if measurement == Measurement.TIME:
            self.fields["hold_min_s"].required = True
            if not self.instance.hold_min_s:
                self.initial.setdefault("hold_min_s", 30)
                self.initial.setdefault("hold_max_s", 45)

    def clean(self):
        cleaned = super().clean()
        for low, high, label in (
            ("rep_min", "rep_max", "Reps from"),
            ("hold_min_s", "hold_max_s", "Hold from"),
        ):
            low_value, high_value = cleaned.get(low), cleaned.get(high)
            if low_value and high_value and low_value > high_value:
                self.add_error(high, f"Must be at least “{label}”.")
        return cleaned
