from django import forms

from .models import Exercise


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ("name", "muscle_group", "equipment", "is_bodyweight")

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        # The DB constraint only covers the user's own exercises; also stop a
        # user from creating a copy of a built-in exercise.
        if Exercise.objects.visible_to(self.owner).filter(name__iexact=name).exists():
            raise forms.ValidationError("An exercise with this name already exists.")
        return name

    def save(self, commit=True):
        exercise = super().save(commit=False)
        exercise.owner = self.owner
        if commit:
            exercise.save()
        return exercise
