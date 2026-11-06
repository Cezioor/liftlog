from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext, pgettext_lazy

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
        return self.plan_day.name if self.plan_day else gettext("Workout")

    @property
    def is_finished(self):
        return self.finished_at is not None


class Side(models.TextChoices):
    LEFT = "left", pgettext_lazy("side", "Left")
    RIGHT = "right", pgettext_lazy("side", "Right")


class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")
    # RESTRICT (not PROTECT): an exercise with logged sets can't be deleted on its own,
    # but deleting a whole account (exercises + workouts together) still works.
    exercise = models.ForeignKey(Exercise, on_delete=models.RESTRICT, related_name="+")
    # Set number within this exercise in this workout (1, 2, 3, ...).
    order = models.PositiveSmallIntegerField(default=1)
    # Which fields are filled depends on the exercise's measurement (Stage 1.6):
    #   weight_reps: weight_kg + reps        reps: reps (+ optional added weight_kg)
    #   time: duration_seconds (+ optional weight_kg)   distance_time: distance_m + duration
    # Sets logged before Stage 1.6 are weight + reps and stay exactly as they were.
    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1000"))],
    )
    reps = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    duration_seconds = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(24 * 3600)]
    )
    distance_m = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(1_000_000)]
    )
    # For one-side exercises: "left" / "right"; empty for everything else.
    side = models.CharField(max_length=5, choices=Side.choices, blank=True)
    # How hard the set felt, always stored as RIR = reps in reserve (how many more reps
    # were possible): 0 = nothing left ... 4 = four or more. Halves come from RPE (8.5 = 1.5).
    # The user's settings only change how it is shown and entered, never the stored value.
    rir = models.DecimalField(
        "reps in reserve",
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("4"))],
    )
    is_warmup = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        from .services import set_text

        return f"{self.exercise.name}: {set_text(self, self.exercise.measurement, long=True)}"


class WorkoutSwap(models.Model):
    """ "Only today": in this workout a plan exercise is done as another variant.

    The plan stays as it is; next time the plan's exercise is back. Sets logged before
    the swap stay with the exercise they were logged with.
    """

    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="swaps")
    plan_exercise = models.ForeignKey(
        "plans.PlanExercise", on_delete=models.CASCADE, related_name="+"
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.RESTRICT, related_name="+")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workout", "plan_exercise"], name="one_swap_per_plan_exercise"
            ),
        ]

    def __str__(self):
        return f"{self.workout}: {self.plan_exercise.exercise} -> {self.exercise}"
