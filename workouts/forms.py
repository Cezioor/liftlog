from decimal import Decimal

from django import forms

from exercises.forms import WeightField
from exercises.models import Measurement

from .models import Side, Workout, WorkoutSet


class DurationField(forms.IntegerField):
    """Seconds, typed as "90", "1:30" or "1:02:05"."""

    def to_python(self, value):
        if isinstance(value, str) and ":" in value:
            parts = value.strip().split(":")
            if not all(p.isdigit() for p in parts) or len(parts) > 3:
                raise forms.ValidationError("Use seconds (90) or minutes:seconds (1:30).")
            seconds = 0
            for part in parts:
                seconds = seconds * 60 + int(part)
            return seconds
        return super().to_python(value)


def _num_input(mode="numeric"):
    # Text inputs with inputmode instead of type="number": number inputs
    # silently drop a comma value in some mobile browsers.
    attrs = {"inputmode": mode, "autocomplete": "off", "class": "num-input"}
    if mode == "numeric":
        attrs["pattern"] = "[0-9]*"
    return forms.TextInput(attrs=attrs)


class WorkoutSetForm(forms.ModelForm):
    """One set. Only the fields that fit the exercise's measurement are kept:

    weight_reps: kg + reps · reps: reps + optional kg · time: seconds + optional kg ·
    distance_time: metres + optional seconds. One-side exercises also get left/right.
    """

    FIELDS_BY_MEASUREMENT = {
        Measurement.WEIGHT_REPS: ["weight_kg", "reps"],
        Measurement.REPS: ["reps", "weight_kg"],
        Measurement.TIME: ["duration_seconds", "weight_kg"],
        Measurement.DISTANCE_TIME: ["distance_m", "duration_seconds"],
    }
    REQUIRED_BY_MEASUREMENT = {
        Measurement.WEIGHT_REPS: {"weight_kg", "reps"},
        Measurement.REPS: {"reps"},
        Measurement.TIME: {"duration_seconds"},
        Measurement.DISTANCE_TIME: {"distance_m"},
    }

    class Meta:
        model = WorkoutSet
        fields = (
            "weight_kg",
            "reps",
            "duration_seconds",
            "distance_m",
            "side",
            "is_warmup",
        )
        field_classes = {"weight_kg": WeightField, "duration_seconds": DurationField}
        labels = {
            "weight_kg": "kg",
            "reps": "Reps",
            "duration_seconds": "Seconds",
            "distance_m": "Metres",
            "side": "Side",
            "is_warmup": "Warm-up",
        }
        widgets = {
            "weight_kg": _num_input("decimal"),
            "reps": _num_input(),
            "duration_seconds": forms.TextInput(
                attrs={"inputmode": "numeric", "autocomplete": "off", "class": "num-input"}
            ),
            "distance_m": _num_input(),
            "side": forms.RadioSelect(attrs={"class": "side-radio"}),
        }

    def __init__(self, *args, measurement=Measurement.WEIGHT_REPS, unilateral=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurement = measurement
        keep = set(self.FIELDS_BY_MEASUREMENT[measurement]) | {"is_warmup"}
        if unilateral:
            keep.add("side")
        for name in list(self.fields):
            if name not in keep:
                del self.fields[name]
        required = self.REQUIRED_BY_MEASUREMENT[measurement]
        for name, field in self.fields.items():
            field.required = name in required or name == "side"
        if "weight_kg" in self.fields and "weight_kg" not in required:
            self.fields["weight_kg"].label = "Added kg"
        if "side" in self.fields:
            # Only left / right, without Django's empty "---------" choice.
            self.fields["side"].choices = Side.choices

    def clean(self):
        cleaned = super().clean()
        # Optional added weight left empty means no added weight.
        if "weight_kg" in self.fields and cleaned.get("weight_kg") is None:
            cleaned["weight_kg"] = Decimal("0")
        return cleaned


class FinishWorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ("note",)
        labels = {"note": "Note (optional)"}
        widgets = {
            "note": forms.Textarea(attrs={"rows": 2, "placeholder": "How did it go?"}),
        }
