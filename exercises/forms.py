from django import forms

from .models import Category, Exercise, Measurement, Muscle
from .services import default_progression_step, find_by_name


class WeightField(forms.DecimalField):
    """Accepts both "62.5" and "62,5" (Polish phone keyboards type a comma)."""

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
        return super().to_python(value)


class ExerciseForm(forms.ModelForm):
    primary_muscles = forms.MultipleChoiceField(
        label="Main muscles",
        choices=Muscle.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "muscle-checkboxes"}),
        help_text="Shown on the muscle map. Empty = based on the muscle group.",
    )
    secondary_muscles = forms.MultipleChoiceField(
        label="Helping muscles",
        choices=Muscle.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "muscle-checkboxes"}),
    )

    class Meta:
        model = Exercise
        fields = (
            "name",
            "aliases",
            "muscle_group",
            "equipment",
            "measurement",
            "category",
            "is_unilateral",
            "is_bodyweight",
            "progression_step_kg",
            "primary_muscles",
            "secondary_muscles",
        )
        field_classes = {"progression_step_kg": WeightField}
        widgets = {
            "aliases": forms.Textarea(attrs={"rows": 2}),
            "progression_step_kg": forms.TextInput(
                attrs={"inputmode": "decimal", "placeholder": "Leave empty for the default"}
            ),
        }

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.fields["progression_step_kg"].help_text = (
            "kg added when every set hits the top of the rep range. "
            "Empty = default: dumbbells 2, legs 5, upper body 2.5."
        )
        # Optional with sensible defaults, so forms opened before Stage 1.6 still save.
        for name in ("measurement", "category"):
            self.fields[name].required = False

    def clean_measurement(self):
        return self.cleaned_data.get("measurement") or Measurement.WEIGHT_REPS

    def clean_category(self):
        return self.cleaned_data.get("category") or Category.STRENGTH

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        # The DB constraint only covers the user's own exercises; also stop a
        # user from creating a copy of a built-in exercise.
        if find_by_name(self.owner, name, exclude_pk=self.instance.pk):
            raise forms.ValidationError("An exercise with this name already exists.")
        return name

    def save(self, commit=True):
        exercise = super().save(commit=False)
        exercise.owner = self.owner
        if self.cleaned_data.get("progression_step_kg") is None:
            exercise.progression_step_kg = default_progression_step(
                exercise.muscle_group, exercise.equipment
            )
        if commit:
            exercise.save()
        return exercise
