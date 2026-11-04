"""Business logic for workouts, kept out of views so it can be tested directly."""

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Max

from exercises.models import Exercise

from .models import WorkoutSet


def format_kg(value):
    """Decimal('62.50') -> '62.5', Decimal('60.00') -> '60'."""
    if value is None:
        return ""
    return f"{value.normalize():f}"


def last_sets(user, exercise, exclude_workout=None):
    """Working sets of `exercise` from the user's most recent finished workout containing it.

    Warm-up sets are left out: they would make the "last time" weight and the
    progression hint misleading.
    """
    sets = WorkoutSet.objects.filter(
        workout__owner=user,
        workout__finished_at__isnull=False,
        exercise=exercise,
        is_warmup=False,
    )
    if exclude_workout is not None:
        sets = sets.exclude(workout=exclude_workout)

    latest = sets.order_by("-workout__finished_at").values_list("workout_id", flat=True).first()
    if latest is None:
        return []
    return list(sets.filter(workout_id=latest).order_by("order", "pk"))


@dataclass(frozen=True)
class ProgressionHint:
    weight_kg: Decimal
    increase: bool
    message: str


def progression_hint(exercise, previous_sets, rep_max):
    """Suggest a weight for today based on last time's sets.

    Rule: if every working set last time reached the top of the rep range,
    add the exercise's progression_step_kg; otherwise keep the weight.
    Returns None when there is nothing to base a hint on.
    """
    if not previous_sets or not rep_max:
        return None

    top_weight = max(s.weight_kg for s in previous_sets)
    hit_top = all(s.reps >= rep_max for s in previous_sets)

    if not hit_top:
        return ProgressionHint(
            weight_kg=top_weight,
            increase=False,
            message=f"Stay at {format_kg(top_weight)} kg until every set reaches {rep_max} reps.",
        )

    if exercise.is_bodyweight and top_weight == 0:
        # No external load to increase; suggest progressing in another way.
        return ProgressionHint(
            weight_kg=top_weight,
            increase=False,
            message=f"All sets hit {rep_max} reps. Add weight or a harder variation.",
        )

    new_weight = top_weight + exercise.progression_step_kg
    return ProgressionHint(
        weight_kg=new_weight,
        increase=True,
        message=f"All sets hit {rep_max} reps last time. Try {format_kg(new_weight)} kg.",
    )


@dataclass(frozen=True)
class SetDefaults:
    weight_kg: Decimal | None
    reps: int | None


def next_set_defaults(current_sets, previous_sets, hint, rep_min=None):
    """Values to pre-fill in the "add set" form so that usually one tap is enough.

    1. Already logged a set today -> repeat it (that's the weight you're using now).
    2. A hint exists -> its weight; reps start at the bottom of the range after an
       increase, otherwise last time's first-set reps.
    3. Only last time -> last time's first set.
    4. Nothing -> empty weight, bottom of the rep range.
    """
    if current_sets:
        last = current_sets[-1]
        return SetDefaults(last.weight_kg, last.reps)

    if hint is not None:
        if hint.increase:
            reps = rep_min or previous_sets[0].reps
        else:
            reps = previous_sets[0].reps
        return SetDefaults(hint.weight_kg, reps)

    if previous_sets:
        return SetDefaults(previous_sets[0].weight_kg, previous_sets[0].reps)

    return SetDefaults(None, rep_min)


def recently_used_exercises(user, limit=6):
    """Exercises the user logged most recently, newest first (for the exercise picker)."""
    ids = list(
        WorkoutSet.objects.filter(workout__owner=user)
        .values("exercise_id")
        .annotate(last_logged=Max("created_at"))
        .order_by("-last_logged")
        .values_list("exercise_id", flat=True)[:limit]
    )
    by_id = Exercise.objects.visible_to(user).in_bulk(ids)
    return [by_id[i] for i in ids if i in by_id]
