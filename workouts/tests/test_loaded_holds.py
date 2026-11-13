"""Loaded holds: a hold whose equipment is the load (hip thrust hold, Pallof hold).

They use the "time" measurement with kg; progression adds weight at the top of the
plan's time range instead of adding seconds forever.
"""

from decimal import Decimal

import pytest

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.forms import WorkoutSetForm
from workouts.models import WorkoutSet
from workouts.services import (
    DEFAULT_LOADED_HOLD_RANGE,
    calibration,
    is_loaded_hold,
    personal_records,
    progression_hint,
)

D = Decimal


@pytest.fixture
def hip_thrust_hold(db):
    return Exercise.objects.create(
        name="Barbell Hip Thrust Hold", muscle_group="glutes", equipment="barbell",
        measurement="time", progression_step_kg=D("5"),
    )  # fmt: skip


@pytest.fixture
def plank(db):
    return Exercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", measurement="time"
    )


def _sets(*pairs):
    """Unsaved sets from (kg, seconds) pairs."""
    return [
        WorkoutSet(order=n, weight_kg=D(kg), duration_seconds=seconds)
        for n, (kg, seconds) in enumerate(pairs, start=1)
    ]


def test_a_hold_with_a_weight_as_equipment_is_loaded(hip_thrust_hold, plank, bench):
    assert is_loaded_hold(hip_thrust_hold)
    assert not is_loaded_hold(plank)  # extra kg on a plank stay optional
    assert not is_loaded_hold(bench)  # not a hold


def test_every_hold_at_the_top_of_the_range_adds_weight(hip_thrust_hold):
    hint = progression_hint(
        hip_thrust_hold, _sets(("60", 45), ("60", 45)), hold_min=30, hold_max=45
    )

    assert (hint.weight_kg, hint.duration_seconds, hint.increase) == (D("65"), 30, True)
    assert "Add 5 kg: 65 kg for 30 s" in hint.message


def test_until_then_the_same_weight_and_longer_holds(hip_thrust_hold):
    hint = progression_hint(
        hip_thrust_hold, _sets(("60", 45), ("60", 35)), hold_min=30, hold_max=45
    )

    assert (hint.weight_kg, hint.duration_seconds, hint.increase) == (D("60"), 45, False)


def test_without_a_plan_a_loaded_hold_uses_the_default_range(hip_thrust_hold):
    """Added to a workout without a plan: 20–40 s, then more weight."""
    assert DEFAULT_LOADED_HOLD_RANGE == (20, 40)

    shorter = progression_hint(hip_thrust_hold, _sets(("60", 30), ("60", 40)))
    assert (shorter.weight_kg, shorter.increase) == (D("60"), False)
    assert "40 s" in shorter.message

    done = progression_hint(hip_thrust_hold, _sets(("60", 40), ("60", 42)))
    assert (done.weight_kg, done.duration_seconds, done.increase) == (D("65"), 20, True)


def test_a_loaded_hold_logged_without_weight_adds_seconds(hip_thrust_hold):
    hint = progression_hint(hip_thrust_hold, _sets(("0", 40)))

    assert (hint.weight_kg, hint.duration_seconds) == (D("0"), 45)


def test_calibration_without_a_plan_stays_in_the_default_range(hip_thrust_hold):
    cal = calibration(hip_thrust_hold, _sets(("40", 90)))

    assert cal.defaults.duration_seconds == 40  # 75% of 90 s would be 68 s


def test_an_unloaded_hold_never_adds_weight(plank):
    hint = progression_hint(plank, _sets(("0", 45), ("0", 45)), hold_min=30, hold_max=45)

    assert (hint.weight_kg, hint.duration_seconds) == (D("0"), 50)


def test_calibration_keeps_the_weight_of_the_test_hold(hip_thrust_hold):
    first = calibration(hip_thrust_hold, [], hold_min=30, hold_max=45)
    assert "light weight" in first.message

    after_test = calibration(hip_thrust_hold, _sets(("40", 60)), hold_min=30, hold_max=45)

    assert (after_test.defaults.weight_kg, after_test.defaults.duration_seconds) == (D("40"), 45)


def _log(user, make_workout, exercise, pairs):
    workout = make_workout(user)
    for number, (kg, seconds) in enumerate(pairs, start=1):
        WorkoutSet.objects.create(
            workout=workout, exercise=exercise, order=number, weight_kg=D(kg),
            duration_seconds=seconds,
        )  # fmt: skip


def _heaviest(user, exercise):
    return {r.label: r.value_text for r in personal_records(user, exercise)}.get("Heaviest hold")


@pytest.mark.django_db
def test_records_add_the_heaviest_hold_as_weight_and_time(user, make_workout, hip_thrust_hold):
    _log(user, make_workout, hip_thrust_hold, [("40", 60), ("60", 30)])

    labels = [r.label for r in personal_records(user, hip_thrust_hold)]
    assert labels == ["Longest hold", "Heaviest hold"]
    assert _heaviest(user, hip_thrust_hold) == "60 kg × 30 s"


@pytest.mark.django_db
def test_a_very_short_heavy_hold_is_not_the_heaviest_hold(user, make_workout, hip_thrust_hold):
    """Without a plan a record hold lasts at least 10 s."""
    _log(user, make_workout, hip_thrust_hold, [("100", 3), ("60", 10)])

    assert _heaviest(user, hip_thrust_hold) == "60 kg × 10 s"


@pytest.mark.django_db
def test_the_heaviest_hold_lasts_at_least_the_plans_minimum(user, make_workout, hip_thrust_hold):
    plan = Plan.objects.create(owner=user, name="Glutes", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="A")
    PlanExercise.objects.create(day=day, exercise=hip_thrust_hold, hold_min_s=30, hold_max_s=45)
    _log(user, make_workout, hip_thrust_hold, [("80", 20), ("70", 30)])

    assert _heaviest(user, hip_thrust_hold) == "70 kg × 30 s"


@pytest.mark.django_db
def test_an_unloaded_hold_has_no_heaviest_hold(user, make_workout, plank):
    _log(user, make_workout, plank, [("10", 60)])

    assert [r.label for r in personal_records(user, plank)] == ["Longest hold"]


def test_the_weight_field_of_a_loaded_hold_is_plain_kg():
    loaded = WorkoutSetForm(measurement="time", loaded=True)
    plank = WorkoutSetForm(measurement="time")

    assert loaded.fields["weight_kg"].label == "kg"
    assert plank.fields["weight_kg"].label == "Added kg"
    assert not loaded.fields["weight_kg"].required  # a first test hold may be unloaded
