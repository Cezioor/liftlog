"""Set rating: stored as RIR, entered and shown as simple words, RIR or RPE."""

from decimal import Decimal

import pytest
from django.urls import reverse

from accounts.models import EffortScale
from accounts.services import get_user_settings
from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.forms import WorkoutSetForm
from workouts.models import WorkoutSet
from workouts.services import (
    effort_choices,
    effort_text,
    progression_hint,
    rpe_from_rir,
    set_text,
)

HTMX = {"HTTP_HX_REQUEST": "true"}
D = Decimal


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def pull_ups(db):
    return Exercise.objects.create(
        name="Pull-up", muscle_group="back", equipment="bodyweight", measurement="reps"
    )


def _set(reps, rir=None, weight="60"):
    return WorkoutSet(weight_kg=D(weight), reps=reps, rir=None if rir is None else D(str(rir)))


def _scale(user, scale):
    settings = get_user_settings(user)
    settings.effort_scale = scale
    settings.save()


# --- showing a rating ---------------------------------------------------------


@pytest.mark.parametrize(
    "rir, scale, expected",
    [
        ("2", "rir", "@RIR 2"),
        ("4", "rir", "@RIR 4+"),
        ("1.5", "rir", "@RIR 1.5"),
        ("2", "rpe", "@RPE 8"),
        ("1.5", "rpe", "@RPE 8.5"),
        ("4", "rpe", "@RPE 6"),
        ("0", "rpe", "@RPE 10"),
        ("4", "simple", "Easy"),
        ("3", "simple", "Medium"),
        ("2", "simple", "Hard"),
        ("1.5", "simple", "Hard"),
        ("1", "simple", "Hard"),
        ("0.5", "simple", "Max effort"),
        ("0", "simple", "Max effort"),
    ],
)
def test_effort_text(rir, scale, expected):
    assert effort_text(D(rir), scale) == expected


def test_no_rating_no_text():
    assert effort_text(None, "rir") == ""


def test_rpe_is_ten_minus_rir():
    assert rpe_from_rir(D("2")) == D("8")
    assert rpe_from_rir(D("8.5")) == D("1.5")


@pytest.mark.parametrize(
    "scale, expected",
    [
        ("rir", "60 × 8 @RIR 2"),
        ("rpe", "60 × 8 @RPE 8"),
        ("simple", "60 × 8 · Hard"),
        (None, "60 × 8"),
    ],
)
def test_set_text_with_rating(scale, expected):
    assert set_text(_set(8, 2), "weight_reps", scale=scale) == expected


# --- buttons ------------------------------------------------------------------


def test_effort_choices_per_scale():
    assert effort_choices("simple") == [
        ("4", "Easy"),
        ("3", "Medium"),
        ("1.5", "Hard"),
        ("0", "Max effort"),
    ]
    assert effort_choices("rir") == [("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4+")]
    rpe = effort_choices("rpe")
    assert [label for _, label in rpe] == ["6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10"]
    assert rpe[4] == ("2", "8")  # the RPE 8 button saves RIR 2


def test_effort_choices_keep_a_saved_rating_the_scale_has_no_button_for():
    assert ("1.5", "1.5") in effort_choices("rir", current=D("1.5"))
    assert ("2", "Hard (RIR 2)") in effort_choices("simple", current=D("2"))
    assert len(effort_choices("rir", current=D("2"))) == 5  # already there: no duplicate


@pytest.mark.parametrize(
    "scale, value, saved",
    [("simple", "1.5", "1.5"), ("rir", "4", "4"), ("rpe", "1.5", "1.5"), ("rpe", "", None)],
)
def test_form_saves_rir_whatever_the_scale(scale, value, saved):
    form = WorkoutSetForm(
        {"weight_kg": "60", "reps": "8", "rir": value}, measurement="weight_reps",
        effort_scale=scale,
    )  # fmt: skip

    assert form.is_valid(), form.errors
    assert form.cleaned_data["rir"] == (None if saved is None else D(saved))


def test_form_rejects_a_rating_from_outside_the_scale():
    form = WorkoutSetForm(
        {"weight_kg": "60", "reps": "8", "rir": "7"}, measurement="weight_reps", effort_scale="rir"
    )

    assert not form.is_valid()
    assert "rir" in form.errors


def test_time_and_distance_sets_have_no_rating():
    for measurement in ("time", "distance_time"):
        assert "rir" not in WorkoutSetForm(measurement=measurement).fields


@pytest.mark.django_db
def test_edit_form_selects_the_saved_rating(user, make_workout, bench):
    workout = make_workout(user, {bench: [(60, 8)]})
    workout_set = workout.sets.get()
    workout_set.rir = D("4.0")
    workout_set.save()

    form = WorkoutSetForm(instance=workout_set, effort_scale="rir")

    selected = [radio.data["value"] for radio in form["rir"] if radio.data["selected"]]
    assert selected == ["4"]


# --- screens ------------------------------------------------------------------


@pytest.fixture
def bench_day(user, bench):
    plan = Plan.objects.create(owner=user, name="Plan")
    day = PlanDay.objects.create(plan=plan, name="Push", order=1)
    PlanExercise.objects.create(day=day, exercise=bench, order=1, rep_min=8, rep_max=12)
    return day


@pytest.mark.django_db
def test_logging_a_set_with_a_rating(logged_in, user, make_workout, bench_day, bench):
    workout = make_workout(user, days_ago=0, finished=False, plan_day=bench_day)

    response = logged_in.post(
        reverse("workouts:set_create", args=[workout.pk, bench.pk]),
        {"weight_kg": "60", "reps": "8", "rir": "1.5"},
        **HTMX,
    )

    assert WorkoutSet.objects.get().rir == D("1.5")
    assert "60 × 8 · Hard" in response.content.decode()


@pytest.mark.django_db
def test_switching_scale_changes_only_how_it_looks(logged_in, user, make_workout, bench_day, bench):
    last = make_workout(user, {bench: [(60, 8)]}, days_ago=3)
    last.sets.update(rir=D("2"))
    workout = make_workout(user, days_ago=0, finished=False, plan_day=bench_day)
    url = reverse("workouts:workout_detail", args=[workout.pk])

    shown = {}
    for scale in ("simple", "rir", "rpe"):
        response = logged_in.post(
            reverse("settings"), {"effort_scale": scale, "ios_shortcut_name": "LiftLog Rest"}
        )
        assert response.status_code == 302
        shown[scale] = logged_in.get(url).content.decode()

    assert "60 × 8 · Hard" in shown["simple"]
    assert "60 × 8 @RIR 2" in shown["rir"]
    assert "60 × 8 @RPE 8" in shown["rpe"]
    assert "Effort, 6–10 (RPE)" in shown["rpe"]
    assert WorkoutSet.objects.get(workout=last).rir == D("2")


@pytest.mark.django_db
def test_history_shows_the_rating(logged_in, user, make_workout, bench):
    workout = make_workout(user, {bench: [(60, 8)]})
    workout.sets.update(rir=D("0"))
    _scale(user, EffortScale.RIR)

    summary = logged_in.get(reverse("workouts:workout_detail", args=[workout.pk]))
    detail = logged_in.get(reverse("exercises:exercise_detail", args=[bench.pk]))

    assert "60 kg × 8 @RIR 0" in summary.content.decode()
    assert "60 kg × 8 @RIR 0" in detail.content.decode()


@pytest.mark.django_db
def test_settings_default_to_the_simple_scale(logged_in, user):
    content = logged_in.get(reverse("settings")).content.decode()

    assert get_user_settings(user).effort_scale == "simple"
    assert "Rating your sets" in content


# --- progression hint ---------------------------------------------------------


@pytest.mark.parametrize("rir", [None, 0, 2])
def test_hint_without_reps_to_spare_is_unchanged(bench, rir):
    hint = progression_hint(bench, [_set(12, rir), _set(10)], rep_max=12, rep_min=8)

    assert (hint.increase, hint.weight_kg) == (False, D("60"))


def test_top_of_range_with_three_in_reserve_means_add_weight(bench):
    hint = progression_hint(bench, [_set(12, 3), _set(11)], rep_max=12, rep_min=8)

    assert hint.increase is True
    assert hint.weight_kg == D("62.5")
    assert "3+ more in the tank" in hint.message


def test_max_effort_at_the_bottom_of_the_range_means_stay(bench):
    # Even though the other sets hit the top, the 8-rep max effort wins.
    hint = progression_hint(
        bench, [_set(12), _set(12), _set(8, 0)], rep_max=12, rep_min=8
    )  # fmt: skip

    assert hint.increase is False
    assert hint.weight_kg == D("60")
    assert "Stay at 60 kg" in hint.message


def test_max_effort_above_the_bottom_is_no_stay_signal(bench):
    hint = progression_hint(bench, [_set(12, 0), _set(12, 0)], rep_max=12, rep_min=8)

    assert hint.increase is True


def test_reps_hint_uses_the_rating_too(pull_ups):
    easy = progression_hint(
        pull_ups, [_set(12, 4, weight="0"), _set(10, weight="0")], rep_max=12, rep_min=6
    )
    limit = progression_hint(
        pull_ups, [_set(6, 0, weight="0"), _set(5, weight="0")], rep_max=12, rep_min=6
    )

    assert easy.increase is True
    assert easy.weight_kg == pull_ups.progression_step_kg
    assert (limit.increase, limit.reps) == (False, 6)
    assert "Aim for 6 again" in limit.message
