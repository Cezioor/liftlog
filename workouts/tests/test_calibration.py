"""First time with an exercise: calibration for holds, reps and weights."""

import re
from decimal import Decimal

import pytest
from django.urls import reverse

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import WorkoutSet
from workouts.services import (
    NO_MAX_TEST_NOTE,
    calibration,
    personal_records,
    round_down_to_step,
    working_weight,
)

HTMX = {"HTTP_HX_REQUEST": "true"}
D = Decimal


@pytest.fixture
def plank(db):
    return Exercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", measurement="time"
    )


@pytest.fixture
def side_plank(db):
    return Exercise.objects.create(
        name="Side Plank", muscle_group="core", equipment="bodyweight", measurement="time",
        is_unilateral=True,
    )  # fmt: skip


@pytest.fixture
def push_ups(db):
    return Exercise.objects.create(
        name="Push-up", muscle_group="chest", equipment="bodyweight", measurement="reps"
    )


@pytest.fixture
def curl(db):
    return Exercise.objects.create(
        name="Dumbbell Curl", muscle_group="biceps", equipment="dumbbell"
    )


def _sets(*fields):
    """Unsaved sets in order: dicts of WorkoutSet fields."""
    return [
        WorkoutSet(order=n, **{"weight_kg": D("0"), **f}) for n, f in enumerate(fields, start=1)
    ]


# --- time ---------------------------------------------------------------------


def test_hold_starts_with_a_test_hold(plank):
    cal = calibration(plank, [], hold_min=30, hold_max=45)

    assert "Hold as long as your form stays good" in cal.message
    assert cal.defaults.duration_seconds is None  # the hold timer measures it


@pytest.mark.parametrize(
    "test_hold, hold_min, hold_max, working",
    [
        (60, 30, 45, 45),  # 75% = 45
        (80, 30, 45, 45),  # 75% = 60, kept at the plan's top
        (36, 30, 45, 30),  # 75% = 27, raised to the plan's bottom
        (20, 30, 45, 15),  # can't hold the plan's 30 s yet: 75% of the test
        (50, None, None, 38),  # no plan: just 75%
    ],
)
def test_working_holds_are_75_percent_within_the_plan(
    plank, test_hold, hold_min, hold_max, working
):
    cal = calibration(
        plank, _sets({"duration_seconds": test_hold}), hold_min=hold_min, hold_max=hold_max
    )

    assert cal.defaults.duration_seconds == working
    assert f"Test hold: {test_hold} s" in cal.message or "Test hold: 1:" in cal.message


def test_hold_calibration_stops_pre_filling_once_working_sets_start(plank):
    cal = calibration(plank, _sets({"duration_seconds": 60}, {"duration_seconds": 40}))

    assert cal.defaults is None  # the form repeats the last set, as usual
    assert "Working holds: 45 s" in cal.message


def test_one_side_holds_test_both_sides_and_use_the_weaker(side_plank):
    after_left = calibration(side_plank, _sets({"duration_seconds": 40, "side": "left"}))
    after_both = calibration(
        side_plank,
        _sets({"duration_seconds": 40, "side": "left"}, {"duration_seconds": 30, "side": "right"}),
    )

    assert "other side" in after_left.message
    assert after_left.defaults.side == "right"
    assert after_both.defaults.duration_seconds == 23  # 75% of 30 s, the weaker side
    assert after_both.defaults.side == "left"


# --- reps ---------------------------------------------------------------------


def test_reps_start_with_a_test_set_to_technical_max(push_ups):
    cal = calibration(push_ups, [])

    assert "as many clean reps as you can" in cal.message
    assert "form starts to slip" in cal.message
    assert cal.defaults.reps is None


@pytest.mark.parametrize("test_reps, working", [(10, 7), (15, 11), (20, 14), (1, 1)])
def test_working_reps_are_70_percent(push_ups, test_reps, working):
    cal = calibration(push_ups, _sets({"reps": test_reps}))

    assert cal.defaults.reps == working
    assert f"Working sets: {working} reps" in cal.message


# --- weight × reps ------------------------------------------------------------


def test_barbell_starts_with_the_empty_bar_as_a_warm_up(bench):
    cal = calibration(bench, [], rep_min=8, rep_max=12)

    assert (cal.defaults.weight_kg, cal.defaults.reps, cal.defaults.is_warmup) == (D("20"), 8, True)
    assert "empty bar, 20 kg" in cal.message
    assert "no max test" in cal.message
    assert cal.note == NO_MAX_TEST_NOTE
    assert "injuries" in cal.note


def test_dumbbells_start_light(curl):
    assert calibration(curl, []).defaults.weight_kg == D("5")


@pytest.mark.parametrize(
    "rir, next_weight",
    [("4", D("25")), ("3", D("22.5"))],  # +25% when 4+ left, +10% (at least one step) when 3
)
def test_easy_test_set_suggests_a_heavier_test_set(bench, rir, next_weight):
    cal = calibration(bench, _sets({"weight_kg": D("20"), "reps": 8, "rir": D(rir)}))

    assert cal.defaults.weight_kg == next_weight
    assert cal.defaults.is_warmup is True
    assert "Next test set" in cal.message


def test_unrated_test_set_asks_for_a_rating(bench):
    cal = calibration(bench, _sets({"weight_kg": D("20"), "reps": 8}))

    assert "Rate your test set" in cal.message
    assert cal.defaults.weight_kg == D("20")


def test_first_set_at_rir_2_gives_the_working_weight(bench):
    sets = _sets(
        {"weight_kg": D("20"), "reps": 8, "rir": D("4"), "is_warmup": True},
        {"weight_kg": D("40"), "reps": 8, "rir": D("2"), "is_warmup": True},
    )

    cal = calibration(bench, sets, rep_min=8, rep_max=12)

    # Epley with the reps in reserve: 40 × (1 + (8 + 2) / 30) = 53.3 kg.
    assert cal.estimated_1rm == D("53.3")
    # 12 reps with 2 to spare: 53.3 / (1 + 14/30) = 36.3, rounded down to 2.5 kg -> 35.
    assert cal.defaults == cal.defaults.__class__(D("35.0"), 8, side="", is_warmup=False)
    assert "Estimated max: about 53.3 kg" in cal.message
    assert "35 kg × 8–12" in cal.message


def test_hard_rating_from_the_simple_scale_counts_too(bench):
    cal = calibration(bench, _sets({"weight_kg": D("40"), "reps": 8, "rir": D("1.5")}))

    assert cal.estimated_1rm == D("52.7")  # 40 × (1 + 9.5 / 30)


def test_after_calibration_working_sets_repeat_as_usual(bench):
    sets = _sets(
        {"weight_kg": D("40"), "reps": 8, "rir": D("2"), "is_warmup": True},
        {"weight_kg": D("35"), "reps": 10},
    )

    assert calibration(bench, sets).defaults is None


def test_working_weight_never_below_the_empty_bar(bench):
    cal = calibration(bench, _sets({"weight_kg": D("20"), "reps": 5, "rir": D("0")}))

    assert cal.defaults.weight_kg == D("20")


def test_rounding_and_working_weight():
    assert round_down_to_step(D("62.9"), D("2.5")) == D("62.5")
    assert round_down_to_step(D("36.9"), D("2")) == D("36")
    assert round_down_to_step(D("9.99"), None) == D("7.5")
    assert working_weight(D("100"), 12, D("2.5")) == D("67.5")  # 100 / (1 + 14/30) = 68.2


def test_distance_has_no_calibration(db):
    walk = Exercise.objects.create(
        name="Walk", muscle_group="forearms", equipment="other", measurement="distance_time"
    )

    assert calibration(walk, []) is None


# --- on the workout screen ----------------------------------------------------


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def bench_day(user, bench):
    plan = Plan.objects.create(owner=user, name="Plan")
    day = PlanDay.objects.create(plan=plan, name="Push", order=1)
    PlanExercise.objects.create(day=day, exercise=bench, order=1, rep_min=8, rep_max=12)
    return day


def _input_value(content, name):
    match = re.search(rf'name="{name}" value="([^"]*)"', content)
    return match.group(1) if match else None


@pytest.mark.django_db
def test_calibrating_a_barbell_lift_step_by_step(logged_in, user, make_workout, bench_day, bench):
    workout = make_workout(user, days_ago=0, finished=False, plan_day=bench_day)
    log_url = reverse("workouts:set_create", args=[workout.pk, bench.pk])

    page = logged_in.get(reverse("workouts:workout_detail", args=[workout.pk])).content.decode()
    assert "empty bar, 20 kg" in page and "Why no max test?" in page
    assert _input_value(page, "weight_kg") == "20"
    assert re.search(r'name="is_warmup"[^>]*checked', page)  # test sets are warm-ups

    card = logged_in.post(
        log_url, {"weight_kg": "20", "reps": "8", "rir": "4", "is_warmup": "on"}, **HTMX
    ).content.decode()
    assert "Next test set: 25 kg × 8" in card

    card = logged_in.post(
        log_url, {"weight_kg": "40", "reps": "8", "rir": "1.5", "is_warmup": "on"}, **HTMX
    ).content.decode()
    assert "Estimated max: about 52.7 kg" in card
    assert _input_value(card, "weight_kg") == "35"
    assert not re.search(r'name="is_warmup"[^>]*checked', card)

    logged_in.post(log_url, {"weight_kg": "35", "reps": "10"}, **HTMX)
    logged_in.post(reverse("workouts:workout_finish", args=[workout.pk]), {"note": ""})

    # Test sets don't count as records; next time the normal hint takes over.
    records = personal_records(user, bench)
    assert records[0].workout_set.weight_kg == D("35")
    next_workout = make_workout(user, days_ago=0, finished=False, plan_day=bench_day)
    page = logged_in.get(reverse("workouts:workout_detail", args=[next_workout.pk]))
    assert "Estimated max" not in page.content.decode()
    assert "Stay at 35 kg" in page.content.decode()


@pytest.mark.django_db
def test_calibrating_a_hold_on_the_workout_screen(logged_in, user, make_workout, plank):
    plan = Plan.objects.create(owner=user, name="Core")
    day = PlanDay.objects.create(plan=plan, name="Core", order=1)
    PlanExercise.objects.create(day=day, exercise=plank, order=1, hold_min_s=30, hold_max_s=45)
    workout = make_workout(user, days_ago=0, finished=False, plan_day=day)

    card = logged_in.post(
        reverse("workouts:set_create", args=[workout.pk, plank.pk]),
        {"duration_seconds": "52"},
        **HTMX,
    ).content.decode()

    assert "Test hold: 52 s. Working holds: 39 s (about 75%, within your plan" in card
    assert _input_value(card, "duration_seconds") == "39"


@pytest.mark.django_db
def test_no_calibration_with_history(logged_in, user, make_workout, push_ups):
    make_workout(user, {push_ups: [(0, 12)]}, days_ago=2)
    workout = make_workout(user, days_ago=0, finished=False)

    page = logged_in.get(
        reverse("workouts:workout_detail", args=[workout.pk]), {"add": push_ups.pk}
    ).content.decode()

    assert "test set" not in page.lower()
    assert "Aim for 13" in page
