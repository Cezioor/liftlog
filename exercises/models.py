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


class Muscle(models.TextChoices):
    """Individual muscles, named exactly as in free-exercise-db. Drive the muscle map."""

    ABDOMINALS = "abdominals", "Abdominals"
    ABDUCTORS = "abductors", "Abductors"
    ADDUCTORS = "adductors", "Adductors"
    BICEPS = "biceps", "Biceps"
    CALVES = "calves", "Calves"
    CHEST = "chest", "Chest"
    FOREARMS = "forearms", "Forearms"
    GLUTES = "glutes", "Glutes"
    HAMSTRINGS = "hamstrings", "Hamstrings"
    LATS = "lats", "Lats"
    LOWER_BACK = "lower back", "Lower back"
    MIDDLE_BACK = "middle back", "Middle back"
    NECK = "neck", "Neck"
    QUADRICEPS = "quadriceps", "Quadriceps"
    SHOULDERS = "shoulders", "Shoulders"
    TRAPS = "traps", "Traps"
    TRICEPS = "triceps", "Triceps"


class Level(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    EXPERT = "expert", "Expert"


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
    # --- From free-exercise-db (empty for user exercises and unmatched originals) ---
    # Stable id in free-exercise-db, e.g. "Barbell_Squat". The importer matches on it.
    source_id = models.CharField(max_length=120, unique=True, null=True, blank=True, editable=False)
    # The exercise's name in free-exercise-db. Matched originals keep their own name,
    # so this one is added to the search text: "EZ-Bar Skullcrusher" finds "Skull Crusher".
    source_name = models.CharField(max_length=120, blank=True, editable=False)
    primary_muscles = models.JSONField("main muscles", default=list, blank=True)
    secondary_muscles = models.JSONField("helping muscles", default=list, blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)
    category = models.CharField(max_length=30, blank=True)  # strength, stretching, cardio, ...
    mechanic = models.CharField(max_length=20, blank=True)  # compound / isolation
    instructions = models.JSONField(default=list, blank=True)  # list of steps
    images = models.JSONField(default=list, blank=True)  # paths like "Barbell_Squat/0.jpg"
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
        self.search_text = normalize(f"{self.name}, {self.aliases}, {self.source_name}")
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = {*kwargs["update_fields"], "search_text"}
        super().save(*args, **kwargs)

    @property
    def image_urls(self):
        """Absolute image URLs on jsDelivr, pinned to one free-exercise-db commit."""
        from .free_db import image_url

        return [image_url(path) for path in self.images]

    @property
    def thumbnail_url(self):
        return self.image_urls[0] if self.images else ""

    @property
    def primary_alias(self):
        """First of the other names (the main Polish name), shown under the name."""
        return self.aliases.split(",")[0].strip()

    @property
    def is_builtin(self):
        return self.owner_id is None
