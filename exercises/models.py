from django.conf import settings
from django.db import models
from django.db.models import Q


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
    muscle_group = models.CharField(max_length=20, choices=MuscleGroup.choices)
    equipment = models.CharField(max_length=20, choices=Equipment.choices)
    is_bodyweight = models.BooleanField(default=False)
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

    @property
    def is_builtin(self):
        return self.owner_id is None
