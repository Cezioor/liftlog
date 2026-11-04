from django import forms

from exercises.forms import WeightField

from .models import Workout, WorkoutSet


class WorkoutSetForm(forms.ModelForm):
    class Meta:
        model = WorkoutSet
        fields = ("weight_kg", "reps", "is_warmup")
        field_classes = {"weight_kg": WeightField}
        labels = {"weight_kg": "kg", "reps": "Reps", "is_warmup": "Warm-up"}
        widgets = {
            # Text inputs with inputmode instead of type="number": number inputs
            # silently drop a comma value in some mobile browsers.
            "weight_kg": forms.TextInput(
                attrs={"inputmode": "decimal", "autocomplete": "off", "class": "num-input"}
            ),
            "reps": forms.TextInput(
                attrs={
                    "inputmode": "numeric",
                    "pattern": "[0-9]*",
                    "autocomplete": "off",
                    "class": "num-input",
                }
            ),
        }


class FinishWorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ("note",)
        labels = {"note": "Note (optional)"}
        widgets = {
            "note": forms.Textarea(attrs={"rows": 2, "placeholder": "How did it go?"}),
        }
