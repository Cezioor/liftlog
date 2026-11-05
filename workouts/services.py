"""Business logic for workouts, kept out of views so it can be tested directly.

Stage 1.6: every exercise has a measurement type and these functions handle all four:

  weight_reps     kg × reps                  hint: + progression step (kg)
  reps            reps (+ optional kg)       hint: + 1 rep (or + kg once the range is topped)
  time            seconds (+ optional kg)    hint: + 5 s
  distance_time   metres + seconds           hint: beat last time (no automatic number)

Sets logged before Stage 1.6 are weight × reps; they keep showing as such.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Max

from exercises.models import Exercise, Measurement

from .models import Side, WorkoutSet

HOLD_STEP_SECONDS = 5


# --- formatting -----------------------------------------------------------


def format_kg(value):
    """Decimal('62.50') -> '62.5', Decimal('60.00') -> '60'."""
    if value is None:
        return ""
    return f"{value.normalize():f}"


def format_duration(seconds):
    """45 -> '45 s', 90 -> '1:30', 3725 -> '1:02:05'."""
    if seconds is None:
        return ""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} s"
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def set_text(workout_set, measurement, long=False):
    """How a set reads on screen, based on the fields it actually has.

    Old weight × reps sets therefore look the same even after their exercise
    changed type. `long` adds the "kg" unit for weight × reps (summaries, history).
    """
    s = workout_set
    weight = s.weight_kg or Decimal("0")
    added = f" +{format_kg(weight)} kg" if weight > 0 else ""
    side = {Side.LEFT: "L ", Side.RIGHT: "R "}.get(s.side, "")

    if s.distance_m is not None:
        text = f"{s.distance_m} m"
        if s.duration_seconds:
            text += f" in {format_duration(s.duration_seconds)}"
        return side + text + added
    if s.duration_seconds is not None:
        return side + format_duration(s.duration_seconds) + added
    if s.reps is None:
        return side + "–"
    if measurement == Measurement.REPS:
        return f"{side}{s.reps} reps{added}"
    # weight × reps, including old-style sets of exercises that changed type later
    unit = " kg" if long else ""
    return f"{side}{format_kg(weight)}{unit} × {s.reps}"


# --- "last time" ----------------------------------------------------------


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


def _measured(sets, measurement):
    """Only the sets that have the values this measurement needs (skips old-style sets)."""
    if measurement == Measurement.TIME:
        return [s for s in sets if s.duration_seconds]
    if measurement == Measurement.DISTANCE_TIME:
        return [s for s in sets if s.distance_m]
    return [s for s in sets if s.reps is not None]


# --- progression hint -----------------------------------------------------


@dataclass(frozen=True)
class ProgressionHint:
    weight_kg: Decimal | None
    increase: bool
    message: str
    reps: int | None = None
    duration_seconds: int | None = None


def progression_hint(exercise, previous_sets, rep_max=None, hold_max=None):
    """Suggest today's target from last time's sets, according to the exercise's type.

    Returns None when there is nothing to base a hint on. A hint is a suggestion,
    never forced: the form only gets pre-filled with it.
    """
    measurement = exercise.measurement
    sets = _measured(previous_sets, measurement)
    if not sets:
        return None
    if measurement == Measurement.REPS:
        return _reps_hint(exercise, sets, rep_max)
    if measurement == Measurement.TIME:
        return _time_hint(sets, hold_max)
    if measurement == Measurement.DISTANCE_TIME:
        return _distance_hint(sets)
    return _weight_hint(exercise, sets, rep_max)


def _weight_hint(exercise, sets, rep_max):
    """+ progression step when every set reached the top of the rep range."""
    if not rep_max:
        return None
    top_weight = max(s.weight_kg for s in sets)
    if not all(s.reps >= rep_max for s in sets):
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


def _reps_hint(exercise, sets, rep_max):
    """One more rep than last time's best; once every set tops the range, add weight."""
    best = max(s.reps for s in sets)
    added = max(s.weight_kg or Decimal("0") for s in sets)
    if rep_max and all(s.reps >= rep_max for s in sets):
        new_weight = added + exercise.progression_step_kg
        return ProgressionHint(
            weight_kg=new_weight,
            increase=True,
            reps=None,
            message=f"All sets hit {rep_max} reps. "
            f"Try +{format_kg(new_weight)} kg added weight or a harder variation.",
        )
    target = best + 1
    if rep_max:
        target = min(target, rep_max)
    return ProgressionHint(
        weight_kg=added,
        increase=True,
        reps=target,
        message=f"Best set last time: {best} reps. Aim for {target}.",
    )


def _time_hint(sets, hold_max):
    """+5 s over last time's longest hold, once every hold reached the target."""
    best = max(s.duration_seconds for s in sets)
    added = max(s.weight_kg or Decimal("0") for s in sets)
    if hold_max and not all(s.duration_seconds >= hold_max for s in sets):
        return ProgressionHint(
            weight_kg=added,
            increase=False,
            duration_seconds=best,
            message=f"Keep holding {format_duration(best)} until every set reaches "
            f"{format_duration(hold_max)}.",
        )
    target = best + HOLD_STEP_SECONDS
    return ProgressionHint(
        weight_kg=added,
        increase=True,
        duration_seconds=target,
        message=f"Longest hold last time: {format_duration(best)}. "
        f"Try {format_duration(target)} (+{HOLD_STEP_SECONDS} s).",
    )


def _distance_hint(sets):
    best = max(sets, key=lambda s: (s.distance_m, -(s.duration_seconds or 0)))
    text = f"{best.distance_m} m"
    if best.duration_seconds:
        text += f" in {format_duration(best.duration_seconds)}"
    return ProgressionHint(
        weight_kg=None,
        increase=False,
        message=f"Best last time: {text}. Go a little farther or a little faster.",
    )


# --- pre-filled form ------------------------------------------------------


@dataclass(frozen=True)
class SetDefaults:
    weight_kg: Decimal | None
    reps: int | None
    duration_seconds: int | None = None
    distance_m: int | None = None
    side: str = ""


def _other_side(side):
    return Side.RIGHT if side == Side.LEFT else Side.LEFT


def next_set_defaults(
    current_sets,
    previous_sets,
    hint,
    rep_min=None,
    measurement=Measurement.WEIGHT_REPS,
    hold_min=None,
    unilateral=False,
):
    """Values to pre-fill in the "add set" form so that usually one tap is enough.

    1. Already logged a set today -> repeat it (that's what you're doing now);
       for one-side exercises switch to the other side.
    2. A hint exists -> its values.
    3. Only last time -> last time's first set.
    4. Nothing -> the plan's minimum target, if any.
    """
    first_side = Side.LEFT if unilateral else ""
    if current_sets:
        last = current_sets[-1]
        return SetDefaults(
            _optional_kg(last.weight_kg, measurement),
            last.reps,
            last.duration_seconds,
            last.distance_m,
            _other_side(last.side) if unilateral else "",
        )

    previous = _measured(previous_sets, measurement)
    first = previous[0] if previous else None

    if measurement == Measurement.WEIGHT_REPS:
        if hint is not None:
            reps = (rep_min or first.reps) if hint.increase else first.reps
            return SetDefaults(hint.weight_kg, reps, side=first_side)
        if first:
            return SetDefaults(first.weight_kg, first.reps, side=first_side)
        return SetDefaults(None, rep_min, side=first_side)

    if measurement == Measurement.REPS:
        if hint is not None:
            reps = hint.reps or rep_min or first.reps
            return SetDefaults(_optional_kg(hint.weight_kg, measurement), reps, side=first_side)
        if first:
            return SetDefaults(
                _optional_kg(first.weight_kg, measurement), first.reps, side=first_side
            )
        return SetDefaults(None, rep_min, side=first_side)

    if measurement == Measurement.TIME:
        if hint is not None:
            return SetDefaults(
                _optional_kg(hint.weight_kg, measurement),
                None,
                hint.duration_seconds,
                side=first_side,
            )
        if first:
            return SetDefaults(
                _optional_kg(first.weight_kg, measurement),
                None,
                first.duration_seconds,
                side=first_side,
            )
        return SetDefaults(None, None, hold_min, side=first_side)

    # distance_time: repeat last time's best effort
    if first:
        return SetDefaults(None, None, first.duration_seconds, first.distance_m, first_side)
    return SetDefaults(None, None, None, None, first_side)


def _optional_kg(weight, measurement):
    """For types where weight is optional, 0 kg means "no added weight": leave the field empty."""
    if measurement != Measurement.WEIGHT_REPS and not weight:
        return None
    return weight


# --- records --------------------------------------------------------------


def epley_1rm(weight_kg, reps):
    """Estimated one-rep max (Epley): w × (1 + reps / 30), rounded to 0.1 kg."""
    if not weight_kg or not reps:
        return None
    value = Decimal(weight_kg) * (1 + Decimal(reps) / 30)
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Record:
    label: str
    value_text: str
    workout_set: WorkoutSet


def personal_records(user, exercise):
    """Best results per type from the user's finished workouts (warm-ups excluded).

    weight_reps: best estimated 1RM and heaviest set; reps: most reps in a set;
    time: longest hold; distance_time: longest distance.
    """
    sets = list(
        WorkoutSet.objects.filter(
            workout__owner=user,
            workout__finished_at__isnull=False,
            exercise=exercise,
            is_warmup=False,
        ).select_related("workout")
    )
    measurement = exercise.measurement
    records = []

    if measurement == Measurement.TIME:
        timed = [s for s in sets if s.duration_seconds]
        if timed:
            best = max(timed, key=lambda s: (s.duration_seconds, s.weight_kg))
            records.append(Record("Longest hold", set_text(best, measurement, long=True), best))
    elif measurement == Measurement.DISTANCE_TIME:
        far = [s for s in sets if s.distance_m]
        if far:
            best = max(far, key=lambda s: (s.distance_m, -(s.duration_seconds or 10**9)))
            records.append(Record("Longest distance", set_text(best, measurement), best))
    elif measurement == Measurement.REPS:
        counted = [s for s in sets if s.reps]
        if counted:
            best = max(counted, key=lambda s: (s.reps, s.weight_kg))
            records.append(Record("Most reps", set_text(best, measurement), best))
    else:
        lifted = [s for s in sets if s.reps and s.weight_kg]
        if lifted:
            best = max(lifted, key=lambda s: (epley_1rm(s.weight_kg, s.reps), s.weight_kg))
            e1rm = format_kg(epley_1rm(best.weight_kg, best.reps))
            records.append(
                Record(
                    "Best estimated 1RM",
                    f"{e1rm} kg ({set_text(best, measurement, long=True)})",
                    best,
                )
            )
            heaviest = max(lifted, key=lambda s: (s.weight_kg, s.reps))
            records.append(
                Record("Heaviest set", set_text(heaviest, measurement, long=True), heaviest)
            )
    return records


# --- picker ---------------------------------------------------------------


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
