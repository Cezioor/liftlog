from decimal import Decimal

import pytest

from exercises.models import Exercise
from workouts.models import WorkoutSet
from workouts.services import (
    ProgressionHint,
    SetDefaults,
    format_kg,
    last_sets,
    next_set_defaults,
    progression_hint,
)


def _sets(*pairs):
    """Unsaved WorkoutSet objects, enough for the pure functions."""
    return [WorkoutSet(weight_kg=Decimal(str(w)), reps=r) for w, r in pairs]


def _pairs(sets):
    return [(format_kg(s.weight_kg), s.reps) for s in sets]


# --- format_kg ------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [(Decimal("60.00"), "60"), (Decimal("62.50"), "62.5"), (Decimal("0"), "0"), (None, "")],
)
def test_format_kg(value, expected):
    assert format_kg(value) == expected


# --- last_sets ------------------------------------------------------------


@pytest.mark.django_db
def test_last_sets_returns_most_recent_finished_workout(user, bench, make_workout):
    make_workout(user, {bench: [(50, 10), (50, 9)]}, days_ago=7)
    make_workout(user, {bench: [(55, 8), (55, 8), (55, 7)]}, days_ago=2)

    assert _pairs(last_sets(user, bench)) == [("55", 8), ("55", 8), ("55", 7)]


@pytest.mark.django_db
def test_last_sets_skips_workouts_without_that_exercise(user, bench, squat, make_workout):
    make_workout(user, {bench: [(50, 10)]}, days_ago=5)
    make_workout(user, {squat: [(100, 5)]}, days_ago=1)  # newer, but no bench

    assert _pairs(last_sets(user, bench)) == [("50", 10)]


@pytest.mark.django_db
def test_last_sets_ignores_unfinished_and_current_workout(user, bench, make_workout):
    make_workout(user, {bench: [(50, 10)]}, days_ago=3)
    current = make_workout(user, {bench: [(70, 3)]}, days_ago=0, finished=False)

    assert _pairs(last_sets(user, bench, exclude_workout=current)) == [("50", 10)]
    assert _pairs(last_sets(user, bench)) == [("50", 10)]


@pytest.mark.django_db
def test_last_sets_ignores_other_users(user, other_user, bench, make_workout):
    make_workout(other_user, {bench: [(100, 5)]}, days_ago=1)

    assert last_sets(user, bench) == []


@pytest.mark.django_db
def test_last_sets_leaves_out_warmups(user, bench, make_workout):
    make_workout(user, {bench: [(20, 10, True), (40, 5, True), (60, 8), (60, 8)]})

    assert _pairs(last_sets(user, bench)) == [("60", 8), ("60", 8)]


@pytest.mark.django_db
def test_last_sets_empty_when_never_done(user, bench):
    assert last_sets(user, bench) == []


# --- progression_hint -----------------------------------------------------


def test_hint_adds_2_5_kg_for_upper_body_when_all_sets_hit_top(bench):
    hint = progression_hint(bench, _sets((60, 12), (60, 12), (60, 12)), rep_max=12)

    assert hint.increase is True
    assert hint.weight_kg == Decimal("62.5")
    assert "62.5 kg" in hint.message


def test_hint_adds_5_kg_for_lower_body(squat):
    hint = progression_hint(squat, _sets((100, 8), (100, 9)), rep_max=8)

    assert hint.increase is True
    assert hint.weight_kg == Decimal("105")


def test_hint_keeps_weight_when_any_set_missed_top(bench):
    hint = progression_hint(bench, _sets((60, 12), (60, 11), (60, 10)), rep_max=12)

    assert hint.increase is False
    assert hint.weight_kg == Decimal("60")


def test_hint_uses_heaviest_weight_from_last_time(bench):
    hint = progression_hint(bench, _sets((60, 12), (65, 12)), rep_max=12)

    assert hint.weight_kg == Decimal("67.5")


def test_hint_uses_2_kg_for_dumbbells(db):
    curl = Exercise.objects.create(name="DB Curl", muscle_group="biceps", equipment="dumbbell")

    hint = progression_hint(curl, _sets((14, 12), (14, 12)), rep_max=12)

    assert hint.weight_kg == Decimal("16")


def test_hint_uses_the_users_own_step(bench):
    bench.progression_step_kg = Decimal("1.25")

    hint = progression_hint(bench, _sets((60, 12)), rep_max=12)

    assert hint.weight_kg == Decimal("61.25")
    assert "61.25 kg" in hint.message


def test_no_hint_without_history_or_rep_range(bench):
    assert progression_hint(bench, [], rep_max=12) is None
    assert progression_hint(bench, _sets((60, 12)), rep_max=None) is None


def test_bodyweight_without_load_does_not_add_kg(pull_up):
    hint = progression_hint(pull_up, _sets((0, 10), (0, 10)), rep_max=10)

    assert hint.increase is False
    assert hint.weight_kg == Decimal("0")


def test_weighted_bodyweight_exercise_progresses_normally(pull_up):
    hint = progression_hint(pull_up, _sets((10, 8), (10, 8)), rep_max=8)

    assert hint.weight_kg == Decimal("12.5")


# --- next_set_defaults ----------------------------------------------------


def test_defaults_repeat_set_already_logged_today():
    today = _sets((62.5, 9))
    hint = ProgressionHint(Decimal("62.5"), True, "")

    assert next_set_defaults(today, _sets((60, 12)), hint, rep_min=8) == SetDefaults(
        Decimal("62.5"), 9
    )


def test_defaults_after_increase_start_at_bottom_of_range():
    hint = ProgressionHint(Decimal("62.5"), True, "")

    assert next_set_defaults([], _sets((60, 12)), hint, rep_min=8) == SetDefaults(
        Decimal("62.5"), 8
    )


def test_defaults_without_increase_use_last_reps():
    hint = ProgressionHint(Decimal("60"), False, "")

    assert next_set_defaults([], _sets((60, 10), (60, 9)), hint, rep_min=8) == SetDefaults(
        Decimal("60"), 10
    )


def test_defaults_without_hint_use_last_time():
    assert next_set_defaults([], _sets((40, 15)), None) == SetDefaults(Decimal("40"), 15)


def test_defaults_for_a_new_exercise():
    assert next_set_defaults([], [], None, rep_min=8) == SetDefaults(None, 8)
    assert next_set_defaults([], [], None) == SetDefaults(None, None)
