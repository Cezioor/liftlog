from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from exercises.models import Exercise


class Plan(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plans"
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "-created_at"]
        constraints = [
            # At most one active plan per user; its days appear on the home screen.
            models.UniqueConstraint(
                fields=["owner"],
                condition=Q(is_active=True),
                name="one_active_plan_per_user",
            ),
        ]

    def __str__(self):
        return self.name

    def activate(self):
        Plan.objects.filter(owner=self.owner, is_active=True).exclude(pk=self.pk).update(
            is_active=False
        )
        self.is_active = True
        self.save(update_fields=["is_active"])


class PlanDay(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="days")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.plan.name} – {self.name}"


class PlanExercise(models.Model):
    day = models.ForeignKey(PlanDay, on_delete=models.CASCADE, related_name="exercises")
    # RESTRICT: an exercise used in a plan can't be deleted by accident, but deleting
    # the whole account (its exercises and plans together) still works.
    exercise = models.ForeignKey(Exercise, on_delete=models.RESTRICT, related_name="+")
    order = models.PositiveIntegerField(default=0)
    target_sets = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    rep_min = models.PositiveSmallIntegerField(
        default=8, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    rep_max = models.PositiveSmallIntegerField(
        default=12, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    rest_seconds = models.PositiveSmallIntegerField(default=90, validators=[MaxValueValidator(900)])
    # Targets for other measurement types (Stage 1.6); rep_min/rep_max are used for
    # weight_reps and reps exercises.
    hold_min_s = models.PositiveSmallIntegerField(
        "hold from (s)", null=True, blank=True, validators=[MinValueValidator(1)]
    )
    hold_max_s = models.PositiveSmallIntegerField(
        "hold to (s)", null=True, blank=True, validators=[MinValueValidator(1)]
    )
    target_distance_m = models.PositiveIntegerField(
        "distance (m)", null=True, blank=True, validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(rep_min__lte=models.F("rep_max")),
                name="rep_min_lte_rep_max",
            ),
        ]

    def __str__(self):
        return f"{self.exercise.name} {self.target_sets}×{self.rep_min}–{self.rep_max}"

    @property
    def rep_range(self):
        if self.rep_min == self.rep_max:
            return str(self.rep_min)
        return f"{self.rep_min}–{self.rep_max}"

    @property
    def target_label(self):
        """The per-set target in the exercise's own unit: "8–12 reps", "30–45 s", "40 m"."""
        measurement = self.exercise.measurement
        if measurement == "time":
            if not self.hold_min_s:
                return ""
            if not self.hold_max_s or self.hold_max_s == self.hold_min_s:
                return f"{self.hold_min_s} s"
            return f"{self.hold_min_s}–{self.hold_max_s} s"
        if measurement == "distance_time":
            return f"{self.target_distance_m} m" if self.target_distance_m else ""
        return f"{self.rep_range} reps"
