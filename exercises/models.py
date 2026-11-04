from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .text import normalize


class MuscleGroup(models.TextChoices):
    CHEST = "chest", "Chest"
    BACK = "back", "Back"
    SHOULDERS = "shoulders", "Shoulders"
    BICEPS = "biceps", "Biceps"
    TRICEPS = "triceps", "Triceps"
    FOREARMS = "forearms", "Forearms"
    QUADS = "quads", "Quads"
    HAMSTRINGS = "hamstrings", "Hamstrings"
    GLUTES = "glutes", "Glutes"
    CALVES = "calves", "Calves"
    CORE = "core", "Core"
    FULL_BODY = "full_body", "Full body"
    # Used by "Add my own: …" in the picker when no muscle group filter is chosen.
    OTHER = "other", "Other"


class Equipment(models.TextChoices):
    BARBELL = "barbell", "Barbell"
    DUMBBELL = "dumbbell", "Dumbbell"
    MACHINE = "machine", "Machine"
    CABLE = "cable", "Cable"
    KETTLEBELL = "kettlebell", "Kettlebell"
    BAND = "band", "Resistance band"
    BODYWEIGHT = "bodyweight", "Bodyweight"
    OTHER = "other", "Other"


class ExerciseQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Built-in exercises plus the ones this user created. Never other users' ones."""
        return self.filter(Q(owner__isnull=True) | Q(owner=user))


class Exercise(models.Model):
    name = models.CharField(max_length=100)
    aliases = models.TextField(
        "other names",
        blank=True,
        help_text="Polish names and synonyms, comma separated, e.g. "
        "“wyciskanie na ławce płaskiej, wyciskanie sztangi”.",
    )
    # name + aliases, lowercased and without diacritics; filled in save().
    # Searching this column works the same on SQLite and Postgres.
    search_text = models.TextField(blank=True, editable=False)
    muscle_group = models.CharField(max_length=20, choices=MuscleGroup.choices)
    equipment = models.CharField(max_length=20, choices=Equipment.choices)
    is_bodyweight = models.BooleanField(default=False)
    # kg added by the progression hint. Left empty, it is filled in save() from
    # exercises.services.default_progression_step.
    progression_step_kg = models.DecimalField(
        "progression step (kg)",
        max_digits=5,
        decimal_places=2,
        blank=True,
        validators=[MinValueValidator(Decimal("0.25")), MaxValueValidator(Decimal("50"))],
        help_text="How much weight to add when you hit the top of the rep range on every set.",
    )
    # null = built-in exercise shared by everyone; otherwise a user's own exercise.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="exercises",
    )

    objects = ExerciseQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        constraints = [
            # A plain unique_together would not work for built-ins, because SQL
            # treats NULLs as distinct, so we need two conditional constraints.
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(owner__isnull=True),
                name="unique_builtin_exercise_name",
            ),
            models.UniqueConstraint(
                fields=["owner", "name"],
                condition=Q(owner__isnull=False),
                name="unique_user_exercise_name",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.progression_step_kg is None:
            # Imported here to avoid a circular import (services imports models).
            from .services import default_progression_step

            self.progression_step_kg = default_progression_step(self.muscle_group, self.equipment)
        self.search_text = normalize(f"{self.name}, {self.aliases}")
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = {*kwargs["update_fields"], "search_text"}
        super().save(*args, **kwargs)

    @property
    def primary_alias(self):
        """First of the other names (the main Polish name), shown under the name."""
        return self.aliases.split(",")[0].strip()

    @property
    def is_builtin(self):
        return self.owner_id is None
