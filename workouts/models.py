from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from exercises.models import Exercise
from plans.models import PlanDay


class Workout(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workouts"
    )
    # SET_NULL: deleting a plan must never delete the training history.
    plan_day = models.ForeignKey(
        PlanDay, null=True, blank=True, on_delete=models.SET_NULL, related_name="workouts"
    )
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            # One workout in progress at a time keeps "resume" unambiguous.
            models.UniqueConstraint(
                fields=["owner"],
                condition=Q(finished_at__isnull=True),
                name="one_unfinished_workout_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.started_at:%Y-%m-%d})"

    @property
    def title(self):
        return self.plan_day.name if self.plan_day else "Workout"

    @property
    def is_finished(self):
        return self.finished_at is not None


class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")
    # RESTRICT (not PROTECT): an exercise with logged sets can't be deleted on its own,
    # but deleting a whole account (exercises + workouts together) still works.
    exercise = models.ForeignKey(Exercise, on_delete=models.RESTRICT, related_name="+")
    # Set number within this exercise in this workout (1, 2, 3, ...).
    order = models.PositiveSmallIntegerField(default=1)
    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1000"))],
    )
    reps = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    is_warmup = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.exercise.name}: {self.weight_kg.normalize():f} kg × {self.reps}"
