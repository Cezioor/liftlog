from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from .text import normalize


class MuscleGroup(models.TextChoices):
    CHEST = "chest", _("Chest")
    BACK = "back", _("Back")
    SHOULDERS = "shoulders", _("Shoulders")
    BICEPS = "biceps", _("Biceps")
    TRICEPS = "triceps", _("Triceps")
    FOREARMS = "forearms", _("Forearms")
    QUADS = "quads", _("Quads")
    HAMSTRINGS = "hamstrings", _("Hamstrings")
    GLUTES = "glutes", _("Glutes")
    CALVES = "calves", _("Calves")
    CORE = "core", _("Core")
    FULL_BODY = "full_body", _("Full body")
    # Used by "Add my own: …" in the picker when no muscle group filter is chosen.
    OTHER = "other", pgettext_lazy("muscle group", "Other")


class Equipment(models.TextChoices):
    BARBELL = "barbell", _("Barbell")
    SMITH = "smith", _("Smith machine")
    DUMBBELL = "dumbbell", _("Dumbbell")
    MACHINE = "machine", _("Machine")
    CABLE = "cable", _("Cable")
    KETTLEBELL = "kettlebell", _("Kettlebell")
    BAND = "band", _("Resistance band")
    PLATE = "plate", _("Weight plate")
    PULLUP_BAR = "pullup_bar", _("Pull-up bar")
    LANDMINE = "landmine", _("Landmine")
    SUSPENSION = "suspension", _("TRX / suspension")
    BODYWEIGHT = "bodyweight", _("Bodyweight")
    OTHER = "other", pgettext_lazy("equipment", "Other")


class Muscle(models.TextChoices):
    """Individual muscles, named exactly as in free-exercise-db. Drive the muscle map."""

    ABDOMINALS = "abdominals", _("Abdominals")
    ABDUCTORS = "abductors", _("Abductors")
    ADDUCTORS = "adductors", _("Adductors")
    BICEPS = "biceps", _("Biceps")
    CALVES = "calves", _("Calves")
    CHEST = "chest", _("Chest")
    FOREARMS = "forearms", _("Forearms")
    GLUTES = "glutes", _("Glutes")
    HAMSTRINGS = "hamstrings", _("Hamstrings")
    LATS = "lats", _("Lats")
    LOWER_BACK = "lower back", _("Lower back")
    MIDDLE_BACK = "middle back", _("Middle back")
    NECK = "neck", _("Neck")
    QUADRICEPS = "quadriceps", _("Quadriceps")
    SHOULDERS = "shoulders", _("Shoulders")
    TRAPS = "traps", _("Traps")
    TRICEPS = "triceps", _("Triceps")


class Measurement(models.TextChoices):
    """What a set of this exercise records; decides which inputs the workout screen shows."""

    WEIGHT_REPS = "weight_reps", _("Weight × reps")
    REPS = "reps", _("Reps")
    TIME = "time", _("Time")
    DISTANCE_TIME = "distance_time", _("Distance + time")


class Category(models.TextChoices):
    STRENGTH = "strength", _("Strength")
    ISOMETRIC = "isometric", _("Isometric")
    MOBILITY = "mobility", _("Stretching / mobility")
    PLYOMETRIC = "plyometric", _("Plyometric")
    MOTOR = "motor", _("Motor control / balance")
    CARDIO = "cardio", _("Cardio")
    REHAB = "rehab", _("Rehab")


class Level(models.TextChoices):
    BEGINNER = "beginner", _("Beginner")
    INTERMEDIATE = "intermediate", _("Intermediate")
    EXPERT = "expert", _("Expert")


class ExerciseQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Built-in exercises plus the ones this user created. Never other users' ones."""
        return self.filter(Q(owner__isnull=True) | Q(owner=user))


class Movement(models.Model):
    """A family of variants of one movement: step-ups with a barbell, dumbbells, on the
    Smith machine… Each variant is its own Exercise with its own history and records.

    Built-in families (owner = null) come from `group_movements`; a user's variant of
    their own exercise starts a family owned by that user.
    """

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="movements",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Exercise(models.Model):
    name = models.CharField(_("name"), max_length=100)
    aliases = models.TextField(
        _("other names"),
        blank=True,
        help_text=_(
            "Polish names and synonyms, comma separated, e.g. "
            "“wyciskanie na ławce płaskiej, wyciskanie sztangi”."
        ),
    )
    # name + aliases, lowercased and without diacritics; filled in save().
    # Searching this column works the same on SQLite and Postgres.
    search_text = models.TextField(blank=True, editable=False)
    muscle_group = models.CharField(_("muscle group"), max_length=20, choices=MuscleGroup.choices)
    equipment = models.CharField(_("equipment"), max_length=20, choices=Equipment.choices)
    is_bodyweight = models.BooleanField(_("is bodyweight"), default=False)
    measurement = models.CharField(
        _("logged as"),
        max_length=20,
        choices=Measurement.choices,
        default=Measurement.WEIGHT_REPS,
        help_text=_("Which fields a set has: kg × reps, reps, time, or distance + time."),
    )
    category = models.CharField(
        _("category"), max_length=20, choices=Category.choices, default=Category.STRENGTH
    )
    is_unilateral = models.BooleanField(
        _("one side at a time"),
        default=False,
        help_text=_("Log left and right separately (e.g. single-leg exercises)."),
    )
    # kg added by the progression hint. Left empty, it is filled in save() from
    # exercises.services.default_progression_step.
    progression_step_kg = models.DecimalField(
        _("progression step (kg)"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        validators=[MinValueValidator(Decimal("0.25")), MaxValueValidator(Decimal("50"))],
        help_text=_("How much weight to add when you hit the top of the rep range on every set."),
    )
    # --- From free-exercise-db (empty for user exercises and unmatched originals) ---
    # Stable id in free-exercise-db, e.g. "Barbell_Squat". The importer matches on it.
    source_id = models.CharField(max_length=120, unique=True, null=True, blank=True, editable=False)
    # The exercise's name in free-exercise-db. Matched originals keep their own name,
    # so this one is added to the search text: "EZ-Bar Skullcrusher" finds "Skull Crusher".
    source_name = models.CharField(max_length=120, blank=True, editable=False)
    primary_muscles = models.JSONField(_("main muscles"), default=list, blank=True)
    secondary_muscles = models.JSONField(_("helping muscles"), default=list, blank=True)
    level = models.CharField(_("level"), max_length=20, choices=Level.choices, blank=True)
    # free-exercise-db's own category (strength, stretching, olympic weightlifting, ...).
    source_category = models.CharField(max_length=30, blank=True, editable=False)
    mechanic = models.CharField(max_length=20, blank=True)  # compound / isolation
    instructions = models.JSONField(default=list, blank=True)  # list of steps
    images = models.JSONField(default=list, blank=True)  # paths like "Barbell_Squat/0.jpg"
    # The family of variants this exercise belongs to (same movement, other equipment).
    # SET_NULL: removing a family never touches the exercises or their history.
    movement = models.ForeignKey(
        Movement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="exercises",
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
