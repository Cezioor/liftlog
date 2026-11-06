"""Business logic for workouts, kept out of views so it can be tested directly.

Stage 1.6: every exercise has a measurement type and these functions handle all four:

  weight_reps     kg × reps                  hint: + progression step (kg)
  reps            reps (+ optional kg)       hint: + 1 rep (or + kg once the range is topped)
  time            seconds (+ optional kg)    hint: + 5 s
  distance_time   metres + seconds           hint: beat last time (no automatic number)

Sets logged before Stage 1.6 are weight × reps; they keep showing as such.

Set rating: every set can carry how hard it felt, stored as RIR (reps in reserve).
The user picks how it is entered and shown: simple words, RIR numbers or RPE.

First time with an exercise (no history yet): `calibration` finds the starting point,
a test hold / test set for time and reps, light rated test sets for weights.
"""

from dataclasses import dataclass
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal

from django.db.models import Max

from exercises.models import Equipment, Exercise, Measurement

from .models import Side, WorkoutSet, WorkoutSwap

HOLD_STEP_SECONDS = 5

# A set at the top of the rep range with this many reps to spare means: clearly add weight.
EASY_RIR = Decimal("3")


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


def set_text(workout_set, measurement, long=False, scale=None):
    """How a set reads on screen, based on the fields it actually has.

    Old weight × reps sets therefore look the same even after their exercise
    changed type. `long` adds the "kg" unit for weight × reps (summaries, history).
    With `scale` (the user's EffortScale) the rating is added: "60 × 8 @RIR 2",
    "60 × 8 · Hard".
    """
    text = _set_values_text(workout_set, measurement, long)
    rating = effort_text(workout_set.rir, scale) if scale else ""
    if not rating:
        return text
    if rating.startswith("@"):
        return f"{text} {rating}"
    return f"{text} · {rating}"


def _set_values_text(workout_set, measurement, long):
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


# --- set rating (stored as RIR) -------------------------------------------

# Simple scale: (stored RIR, label). "Hard" means 1–2 reps left, stored as the middle, 1.5.
SIMPLE_EFFORT = [
    (Decimal("4"), "Easy"),
    (Decimal("3"), "Medium"),
    (Decimal("1.5"), "Hard"),
    (Decimal("0"), "Max effort"),
]
RIR_CHOICES = [Decimal(n) for n in range(5)]  # 0, 1, 2, 3, 4 (= 4 or more)
RPE_CHOICES = [Decimal(n) / 2 for n in range(12, 21)]  # 6, 6.5 ... 10


def rpe_from_rir(rir):
    """RPE = 10 − RIR (RIR 2 = RPE 8). Also works the other way round."""
    return Decimal("10") - rir


def _simple_label(rir):
    if rir >= 4:
        return "Easy"
    if rir >= Decimal("2.5"):
        return "Medium"
    if rir >= 1:
        return "Hard"
    return "Max effort"


def effort_label(rir, scale):
    """The rating alone, as its button shows it: "Hard", "4+", "8.5"."""
    from accounts.models import EffortScale

    if scale == EffortScale.RIR:
        return "4+" if rir >= 4 else format_kg(rir)
    if scale == EffortScale.RPE:
        return format_kg(rpe_from_rir(rir))
    return _simple_label(rir)


def effort_text(rir, scale):
    """The rating next to a set: "@RIR 2", "@RIR 4+", "@RPE 8", "Hard"; "" when not rated."""
    from accounts.models import EffortScale

    if rir is None:
        return ""
    label = effort_label(rir, scale)
    if scale == EffortScale.RIR:
        return f"@RIR {label}"
    if scale == EffortScale.RPE:
        return f"@RPE {label}"
    return label


def effort_choices(scale, current=None):
    """[(stored RIR as text, button label)] for the rating buttons of `scale`.

    `current`, an already saved rating the scale has no button for (e.g. RIR 1.5 on
    the RIR scale), is added so that editing a set never loses its rating.
    """
    from accounts.models import EffortScale

    if scale == EffortScale.RIR:
        values = list(RIR_CHOICES)
    elif scale == EffortScale.RPE:
        values = [rpe_from_rir(rpe) for rpe in RPE_CHOICES]
    else:
        values = [rir for rir, _ in SIMPLE_EFFORT]
    if current is not None and current not in values:
        values = sorted([*values, current], reverse=scale != EffortScale.RIR)
    if scale == EffortScale.SIMPLE:
        labels = dict(SIMPLE_EFFORT)
        return [
            (format_kg(v), labels.get(v) or f"{_simple_label(v)} (RIR {format_kg(v)})")
            for v in values
        ]
    return [(format_kg(v), effort_label(v, scale)) for v in values]


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


def progression_hint(exercise, previous_sets, rep_max=None, hold_max=None, rep_min=None):
    """Suggest today's target from last time's sets, according to the exercise's type.

    Returns None when there is nothing to base a hint on. A hint is a suggestion,
    never forced: the form only gets pre-filled with it.

    Set ratings (RIR) sharpen it for weight × reps and reps:
    a set at the top of the range with 3+ reps to spare -> add weight;
    a set at the bottom of the range with nothing left (RIR 0) -> stay where you are.
    """
    measurement = exercise.measurement
    sets = _measured(previous_sets, measurement)
    if not sets:
        return None
    if measurement == Measurement.REPS:
        return _reps_hint(exercise, sets, rep_max, rep_min)
    if measurement == Measurement.TIME:
        return _time_hint(sets, hold_max)
    if measurement == Measurement.DISTANCE_TIME:
        return _distance_hint(sets)
    return _weight_hint(exercise, sets, rep_max, rep_min)


def _easy_at_top(sets, rep_max):
    """Some set reached the top of the range with 3+ reps to spare."""
    return any(s.reps >= rep_max and s.rir is not None and s.rir >= EASY_RIR for s in sets)


def _limit_at_bottom(sets, rep_min):
    """Some set at (or below) the bottom of the range left nothing in the tank."""
    return bool(rep_min) and any(s.reps <= rep_min and s.rir == 0 for s in sets)


def _weight_hint(exercise, sets, rep_max, rep_min=None):
    """+ progression step when every set reached the top of the rep range, or one did
    with 3+ reps to spare; stay when a set at the bottom of the range was a max effort."""
    if not rep_max:
        return None
    top_weight = max(s.weight_kg for s in sets)
    if _limit_at_bottom(sets, rep_min):
        return ProgressionHint(
            weight_kg=top_weight,
            increase=False,
            message=f"Last time {rep_min} reps took everything you had. "
            f"Stay at {format_kg(top_weight)} kg and add reps first.",
        )
    easy = _easy_at_top(sets, rep_max)
    if not easy and not all(s.reps >= rep_max for s in sets):
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
    if easy:
        message = (
            f"{rep_max} reps with 3+ more in the tank: too light. Try {format_kg(new_weight)} kg."
        )
    else:
        message = f"All sets hit {rep_max} reps last time. Try {format_kg(new_weight)} kg."
    return ProgressionHint(weight_kg=new_weight, increase=True, message=message)


def _reps_hint(exercise, sets, rep_max, rep_min=None):
    """One more rep than last time's best; once every set tops the range (or one did with
    3+ reps to spare), add weight. After a max-effort set at the bottom: same reps again."""
    best = max(s.reps for s in sets)
    added = max(s.weight_kg or Decimal("0") for s in sets)
    if rep_max and (all(s.reps >= rep_max for s in sets) or _easy_at_top(sets, rep_max)):
        new_weight = added + exercise.progression_step_kg
        return ProgressionHint(
            weight_kg=new_weight,
            increase=True,
            reps=None,
            message=f"All sets hit {rep_max} reps. "
            f"Try +{format_kg(new_weight)} kg added weight or a harder variation.",
        )
    if _limit_at_bottom(sets, rep_min):
        return ProgressionHint(
            weight_kg=added,
            increase=False,
            reps=best,
            message=f"Last time {rep_min} reps took everything you had. "
            f"Aim for {best} again with clean reps.",
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
    is_warmup: bool = False


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


# --- first time: calibration -------------------------------------------------

HOLD_WORKING_SHARE = Decimal("0.75")  # working holds: about 75% of the test hold
REPS_WORKING_SHARE = Decimal("0.7")  # working sets: about 70% of the test set
CALIBRATED_AT_RIR = Decimal("2")  # the first test set rated RIR <= 2 gives the estimate
WORKING_RIR = 2  # working weight: the top of the rep range with about 2 reps to spare
DEFAULT_REP_RANGE = (8, 12)
# Light first test sets; for a barbell that's the empty bar.
START_WEIGHT_KG = {
    Equipment.BARBELL: Decimal("20"),
    Equipment.DUMBBELL: Decimal("5"),
    Equipment.KETTLEBELL: Decimal("8"),
    Equipment.CABLE: Decimal("10"),
    Equipment.MACHINE: Decimal("10"),
}
NO_MAX_TEST_NOTE = (
    "Why no max test with weights? The last reps before failure are where form breaks "
    "down and injuries happen. A few light test sets and how hard they felt are enough "
    "to estimate your working weight. Test sets are saved as warm-ups, so they don't "
    "count towards your records."
)


@dataclass(frozen=True)
class Calibration:
    """What to tell the user and pre-fill while finding the starting point.

    `defaults` is None once working sets are under way: then the form simply repeats
    the last set, as usual.
    """

    message: str
    defaults: SetDefaults | None
    note: str = ""
    estimated_1rm: Decimal | None = None


def calibration(exercise, current_sets, rep_min=None, rep_max=None, hold_min=None, hold_max=None):
    """Guide the first session with an exercise, from the sets logged so far today.

    time:          one hold for as long as form is good, then working holds of ~75%
                   (within the plan's range when that's possible);
    reps:          one set to the technical max (until form slips), then ~70% of it;
    weight × reps: no max test. Light test sets (empty bar for a barbell), each rated;
                   the first one rated RIR <= 2 gives an Epley estimate with the reps
                   left in reserve counted in, and from it a working weight for the
                   plan's rep range, rounded down to the exercise's weight step.
    distance:      None (the card keeps its simple first-time tip).
    """
    measurement = exercise.measurement
    side = _next_side(current_sets, exercise.is_unilateral)
    if measurement == Measurement.TIME:
        return _hold_calibration(exercise, current_sets, side, hold_min, hold_max)
    if measurement == Measurement.REPS:
        return _reps_calibration(exercise, current_sets, side)
    if measurement == Measurement.WEIGHT_REPS:
        return _weight_calibration(exercise, current_sets, side, rep_min, rep_max)
    return None


def _next_side(current_sets, unilateral):
    if not unilateral:
        return ""
    return _other_side(current_sets[-1].side) if current_sets else Side.LEFT


def _test_result(sets, value, unilateral):
    """The first set is the test; for one-side exercises, the first set on each side.

    Returns (result, number of test sets). The result is None until every side has
    been tested; with two sides the weaker one counts, so both train at the same level.
    """
    if not unilateral:
        return (value(sets[0]), 1) if sets else (None, 0)
    firsts = {}
    for workout_set in sets:
        firsts.setdefault(workout_set.side, value(workout_set))
    if Side.LEFT in firsts and Side.RIGHT in firsts:
        return min(firsts[Side.LEFT], firsts[Side.RIGHT]), 2
    return None, len(firsts)


def _share(value, share):
    return max(1, int((Decimal(value) * share).to_integral_value(rounding=ROUND_HALF_UP)))


def _hold_calibration(exercise, current_sets, side, hold_min, hold_max):
    sets = [s for s in _measured(current_sets, Measurement.TIME) if not s.is_warmup]
    best, tests = _test_result(sets, lambda s: s.duration_seconds, exercise.is_unilateral)
    if best is None:
        if sets:
            message = "Now the same test hold on the other side."
        else:
            message = (
                "First time: test hold. Hold as long as your form stays good, then stop. "
                "Your working holds are based on it."
            )
        return Calibration(message, SetDefaults(None, None, None, side=side))

    target = _share(best, HOLD_WORKING_SHARE)
    # Stay within the plan's range, but never above what the test showed you can hold.
    if hold_min and hold_min <= best:
        target = max(target, hold_min)
    if hold_max:
        target = min(target, hold_max)
    message = (
        f"Test hold: {format_duration(best)}. Working holds: {format_duration(target)} (about 75%"
    )
    if hold_min and hold_max:
        message += f", within your plan's {hold_min}–{hold_max} s"
    message += ")."
    defaults = SetDefaults(None, None, target, side=side) if len(sets) == tests else None
    return Calibration(message, defaults)


def _reps_calibration(exercise, current_sets, side):
    sets = [s for s in _measured(current_sets, Measurement.REPS) if not s.is_warmup]
    best, tests = _test_result(sets, lambda s: s.reps, exercise.is_unilateral)
    if best is None:
        if sets:
            message = "Now the same test set on the other side."
        else:
            message = (
                "First time: test set. Do as many clean reps as you can and stop when "
                "your form starts to slip. Your working sets are based on it."
            )
        return Calibration(message, SetDefaults(None, None, side=side))

    target = _share(best, REPS_WORKING_SHARE)
    message = f"Test set: {best} reps. Working sets: {target} reps (about 70%)."
    defaults = SetDefaults(None, target, side=side) if len(sets) == tests else None
    return Calibration(message, defaults)


def round_down_to_step(weight, step):
    """62.9 with a 2.5 kg step -> 62.5. Never rounds up, so the suggestion stays safe."""
    step = step or Decimal("2.5")
    return (Decimal(weight) / step).to_integral_value(rounding=ROUND_FLOOR) * step


def working_weight(estimated_1rm, rep_max, step):
    """The weight for `rep_max` reps with about 2 to spare (Epley solved for weight)."""
    weight = estimated_1rm / (1 + Decimal(rep_max + WORKING_RIR) / 30)
    return round_down_to_step(weight, step)


def _next_test_weight(weight, rir, step):
    """After an easy test set: +25% when 4+ reps were left, +10% when 3 were left."""
    step = step or Decimal("2.5")
    factor = Decimal("1.25") if rir >= 4 else Decimal("1.1")
    return max(round_down_to_step(weight * factor, step), weight + step)


def _weight_calibration(exercise, current_sets, side, rep_min, rep_max):
    low, high = rep_min or DEFAULT_REP_RANGE[0], rep_max or DEFAULT_REP_RANGE[1]
    step = exercise.progression_step_kg
    start = START_WEIGHT_KG.get(exercise.equipment)
    sets = [s for s in current_sets if s.reps and s.weight_kg]

    calibrating = next((s for s in sets if s.rir is not None and s.rir <= CALIBRATED_AT_RIR), None)
    if calibrating:
        e1rm = epley_1rm(calibrating.weight_kg, calibrating.reps + calibrating.rir)
        working = max(working_weight(e1rm, high, step), start or Decimal("0"))
        message = (
            f"Estimated max: about {format_kg(e1rm)} kg. Working sets: "
            f"{format_kg(working)} kg × {low}–{high}, stopping with 1–2 reps left."
        )
        started = any(s.order > calibrating.order and not s.is_warmup for s in current_sets)
        defaults = None if started else SetDefaults(working, low, side=side)
        return Calibration(message, defaults, estimated_1rm=e1rm)

    if not current_sets:
        weight = start
        what = "empty bar, 20 kg" if exercise.equipment == Equipment.BARBELL else "a light weight"
        message = (
            f"First time: find your working weight, no max test. "
            f"Do a test set ({what}, {low} reps), then rate how hard it was."
        )
    else:
        last = current_sets[-1]
        weight = last.weight_kg
        if last.rir is None:
            message = "Rate your test set (tap ✎ to add it) so LiftLog can suggest the next weight."
        else:
            weight = _next_test_weight(last.weight_kg, last.rir, step)
            message = f"Still light. Next test set: {format_kg(weight)} kg × {low}, then rate it."
    return Calibration(
        message,
        SetDefaults(weight, low, side=side, is_warmup=True),
        note=NO_MAX_TEST_NOTE,
    )


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


# --- changing the variant during a workout ---------------------------------

ONLY_TODAY = "today"
IN_PLAN_TOO = "plan"


def swapped_exercises(workout):
    """{plan exercise id: exercise done instead today} for "only today" changes."""
    return {
        swap.plan_exercise_id: swap.exercise for swap in workout.swaps.select_related("exercise")
    }


def plan_exercise_for(workout, exercise):
    """The plan entry (targets, rest) behind `exercise` in this workout, if any.

    An exercise swapped in "only today" takes over its plan entry; a plan exercise
    swapped out today has none (its leftover sets show as an extra card).
    """
    if workout.plan_day_id is None:
        return None
    swap = workout.swaps.filter(exercise=exercise).select_related("plan_exercise").first()
    if swap is not None:
        return swap.plan_exercise
    swapped_out = workout.swaps.values_list("plan_exercise_id", flat=True)
    return workout.plan_day.exercises.filter(exercise=exercise).exclude(pk__in=swapped_out).first()


def change_variant_in_workout(workout, plan_exercise, exercise, scope):
    """Do `exercise` instead of the plan's exercise: only today, or in the plan too.

    Sets already logged are never moved: they stay with the variant they were done with.
    """
    if scope == IN_PLAN_TOO:
        plan_exercise.exercise = exercise
        plan_exercise.save(update_fields=["exercise"])
        WorkoutSwap.objects.filter(workout=workout, plan_exercise=plan_exercise).delete()
    elif exercise.pk == plan_exercise.exercise_id:
        # Back to the plan's own exercise: nothing to remember.
        WorkoutSwap.objects.filter(workout=workout, plan_exercise=plan_exercise).delete()
    else:
        WorkoutSwap.objects.update_or_create(
            workout=workout, plan_exercise=plan_exercise, defaults={"exercise": exercise}
        )


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
