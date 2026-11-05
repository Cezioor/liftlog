"""Stage 1.6: exercise types. For each type: "last time", progression hint, records."""

import json
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.urls import reverse

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.forms import WorkoutSetForm
from workouts.models import WorkoutSet
from workouts.services import (
    SetDefaults,
    epley_1rm,
    format_duration,
    last_sets,
    next_set_defaults,
    personal_records,
    progression_hint,
    set_text,
)

HTMX = {"HTTP_HX_REQUEST": "true"}


# --- exercises of every type ------------------------------------------------


@pytest.fixture
def pull_ups(db):
    return Exercise.objects.create(
        name="Pull-up", muscle_group="back", equipment="bodyweight", measurement="reps"
    )


@pytest.fixture
def plank(db):
    return Exercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", measurement="time"
    )


@pytest.fixture
def farmers_walk(db):
    return Exercise.objects.create(
        name="Farmer's Walk", muscle_group="forearms", equipment="dumbbell",
        measurement="distance_time",
    )  # fmt: skip


@pytest.fixture
def copenhagen(db):
    return Exercise.objects.create(
        name="Copenhagen Plank", muscle_group="glutes", equipment="bodyweight",
        measurement="time", is_unilateral=True,
    )  # fmt: skip


def log(user, make_workout, exercise, sets, days_ago=1):
    """sets: list of dicts with WorkoutSet fields."""
    workout = make_workout(user, days_ago=days_ago)
    for number, fields in enumerate(sets, start=1):
        WorkoutSet.objects.create(workout=workout, exercise=exercise, order=number, **fields)
    return workout


def _sets(*field_dicts):
    """Unsaved sets for the pure functions."""
    return [WorkoutSet(**{"weight_kg": Decimal("0"), **f}) for f in field_dicts]


# --- formatting -------------------------------------------------------------


@pytest.mark.parametrize(
    "seconds, expected", [(45, "45 s"), (60, "1:00"), (90, "1:30"), (3725, "1:02:05")]
)
def test_format_duration(seconds, expected):
    assert format_duration(seconds) == expected


@pytest.mark.parametrize(
    "fields, measurement, expected",
    [
        ({"weight_kg": Decimal("60"), "reps": 10}, "weight_reps", "60 × 10"),
        ({"reps": 12}, "reps", "12 reps"),
        ({"reps": 8, "weight_kg": Decimal("10")}, "reps", "8 reps +10 kg"),
        ({"duration_seconds": 45}, "time", "45 s"),
        ({"duration_seconds": 30, "weight_kg": Decimal("5")}, "time", "30 s +5 kg"),
        ({"distance_m": 40, "duration_seconds": 35}, "distance_time", "40 m in 35 s"),
        ({"distance_m": 400}, "distance_time", "400 m"),
        ({"duration_seconds": 30, "side": "left"}, "time", "L 30 s"),
        # An old weight × reps set of an exercise that later became "time" reads as logged.
        ({"weight_kg": Decimal("0"), "reps": 60}, "time", "0 × 60"),
    ],
)
def test_set_text(fields, measurement, expected):
    assert set_text(_sets(fields)[0], measurement) == expected


# --- "last time" for every type ---------------------------------------------


@pytest.mark.django_db
def test_last_time_for_reps(user, make_workout, pull_ups):
    log(user, make_workout, pull_ups, [{"reps": 10}, {"reps": 8}], days_ago=5)
    log(user, make_workout, pull_ups, [{"reps": 11}, {"reps": 9}], days_ago=2)

    assert [s.reps for s in last_sets(user, pull_ups)] == [11, 9]


@pytest.mark.django_db
def test_last_time_for_time(user, make_workout, plank):
    log(user, make_workout, plank, [{"duration_seconds": 45}, {"duration_seconds": 40}])

    assert [s.duration_seconds for s in last_sets(user, plank)] == [45, 40]


@pytest.mark.django_db
def test_last_time_for_distance(user, make_workout, farmers_walk):
    log(user, make_workout, farmers_walk, [{"distance_m": 40, "duration_seconds": 30}])

    assert [(s.distance_m, s.duration_seconds) for s in last_sets(user, farmers_walk)] == [(40, 30)]


@pytest.mark.django_db
def test_last_time_for_one_side_keeps_both_sides(user, make_workout, copenhagen):
    log(
        user,
        make_workout,
        copenhagen,
        [
            {"duration_seconds": 20, "side": "left"},
            {"duration_seconds": 25, "side": "right"},
        ],
    )

    assert [(s.side, s.duration_seconds) for s in last_sets(user, copenhagen)] == [
        ("left", 20),
        ("right", 25),
    ]


# --- progression hints for every type ---------------------------------------


def test_reps_hint_adds_one_rep(pull_ups):
    hint = progression_hint(pull_ups, _sets({"reps": 10}, {"reps": 8}), rep_max=12)

    assert (hint.reps, hint.increase) == (11, True)
    assert "Aim for 11" in hint.message


def test_reps_hint_never_goes_past_the_top_of_the_range(pull_ups):
    hint = progression_hint(pull_ups, _sets({"reps": 12}, {"reps": 10}), rep_max=12)

    assert hint.reps == 12


def test_reps_hint_adds_weight_once_every_set_tops_the_range(pull_ups):
    hint = progression_hint(pull_ups, _sets({"reps": 12}, {"reps": 12}), rep_max=12)

    assert hint.weight_kg == Decimal("2.5")  # bodyweight back exercise: 2.5 kg step
    assert hint.reps is None
    assert "+2.5 kg added weight" in hint.message


def test_reps_hint_without_plan_still_adds_a_rep(pull_ups):
    assert progression_hint(pull_ups, _sets({"reps": 7}), rep_max=None).reps == 8


def test_time_hint_adds_five_seconds(plank):
    hint = progression_hint(plank, _sets({"duration_seconds": 45}, {"duration_seconds": 40}))

    assert (hint.duration_seconds, hint.increase) == (50, True)
    assert "+5 s" in hint.message


def test_time_hint_waits_until_every_hold_reaches_the_target(plank):
    sets = _sets({"duration_seconds": 45}, {"duration_seconds": 35})

    hint = progression_hint(plank, sets, hold_max=45)

    assert (hint.duration_seconds, hint.increase) == (45, False)


def test_time_hint_ignores_old_weight_reps_sets(plank):
    # Logged before Plank became a "time" exercise: nothing to base a hold hint on.
    assert progression_hint(plank, _sets({"weight_kg": Decimal("0"), "reps": 60})) is None


def test_distance_hint_shows_best_effort(farmers_walk):
    sets = _sets(
        {"distance_m": 30, "duration_seconds": 20}, {"distance_m": 40, "duration_seconds": 35}
    )

    hint = progression_hint(farmers_walk, sets)

    assert hint.increase is False
    assert "40 m in 35 s" in hint.message


def test_weight_hint_unchanged(bench):
    sets = [WorkoutSet(weight_kg=Decimal("60"), reps=12) for _ in range(3)]

    assert progression_hint(bench, sets, rep_max=12).weight_kg == Decimal("62.5")


# --- pre-filled values for every type ---------------------------------------


def test_defaults_for_reps_use_hint_and_leave_added_weight_empty(pull_ups):
    previous = _sets({"reps": 10})
    hint = progression_hint(pull_ups, previous, rep_max=12)

    defaults = next_set_defaults([], previous, hint, 8, measurement="reps")

    assert defaults == SetDefaults(None, 11)


def test_defaults_for_time_use_hint(plank):
    previous = _sets({"duration_seconds": 40})
    hint = progression_hint(plank, previous)

    assert next_set_defaults([], previous, hint, measurement="time") == SetDefaults(None, None, 45)


def test_defaults_for_time_without_history_use_plan_minimum():
    assert next_set_defaults([], [], None, measurement="time", hold_min=30) == SetDefaults(
        None, None, 30
    )


def test_defaults_for_distance_repeat_last_time():
    previous = _sets({"distance_m": 40, "duration_seconds": 30})

    assert next_set_defaults([], previous, None, measurement="distance_time") == SetDefaults(
        None, None, 30, 40
    )


def test_defaults_for_one_side_alternate_left_and_right():
    first = next_set_defaults([], [], None, measurement="time", unilateral=True)
    today = _sets({"duration_seconds": 20, "side": "left"})
    second = next_set_defaults(today, [], None, measurement="time", unilateral=True)

    assert (first.side, second.side) == ("left", "right")


# --- records for every type -------------------------------------------------


def test_epley():
    assert epley_1rm(Decimal("100"), 5) == Decimal("116.7")
    assert epley_1rm(Decimal("100"), 0) is None


@pytest.mark.django_db
def test_records_weight_reps(user, make_workout, bench):
    make_workout(user, {bench: [(100, 5), (110, 1), (90, 10)]})

    records = {r.label: r.value_text for r in personal_records(user, bench)}

    # e1RM: 100×5 -> 116.7, 110×1 -> 113.7, 90×10 -> 120.0
    assert records == {
        "Best estimated 1RM": "120 kg (90 kg × 10)",
        "Heaviest set": "110 kg × 1",
    }


@pytest.mark.django_db
def test_records_reps(user, make_workout, pull_ups):
    log(user, make_workout, pull_ups, [{"reps": 12}, {"reps": 9}], days_ago=3)
    log(user, make_workout, pull_ups, [{"reps": 14}], days_ago=1)

    assert [(r.label, r.value_text) for r in personal_records(user, pull_ups)] == [
        ("Most reps", "14 reps")
    ]


@pytest.mark.django_db
def test_records_time(user, make_workout, plank):
    log(user, make_workout, plank, [{"duration_seconds": 90}, {"duration_seconds": 75}])

    assert [(r.label, r.value_text) for r in personal_records(user, plank)] == [
        ("Longest hold", "1:30")
    ]


@pytest.mark.django_db
def test_records_distance(user, make_workout, farmers_walk):
    log(
        user,
        make_workout,
        farmers_walk,
        [{"distance_m": 40, "duration_seconds": 30}, {"distance_m": 60, "duration_seconds": 50}],
    )

    assert [(r.label, r.value_text) for r in personal_records(user, farmers_walk)] == [
        ("Longest distance", "60 m in 50 s")
    ]


@pytest.mark.django_db
def test_records_ignore_warmups_unfinished_workouts_and_other_users(
    user, other_user, make_workout, plank
):
    log(user, make_workout, plank, [{"duration_seconds": 60}])
    log(user, make_workout, plank, [{"duration_seconds": 300, "is_warmup": True}])
    open_workout = make_workout(user, days_ago=0, finished=False)
    WorkoutSet.objects.create(workout=open_workout, exercise=plank, duration_seconds=200)
    log(other_user, make_workout, plank, [{"duration_seconds": 500}])

    assert [r.value_text for r in personal_records(user, plank)] == ["1:00"]


@pytest.mark.django_db
def test_records_empty_without_history(user, plank):
    assert personal_records(user, plank) == []


@pytest.mark.django_db
def test_detail_page_shows_records(client, user, make_workout, plank):
    log(user, make_workout, plank, [{"duration_seconds": 90}])
    client.force_login(user)

    content = client.get(reverse("exercises:exercise_detail", args=[plank.pk])).content.decode()

    assert "Longest hold" in content and "1:30" in content
    assert "Logged as time" in content


# --- the set form shows only the fields of the type --------------------------


@pytest.mark.parametrize(
    "measurement, unilateral, fields",
    [
        ("weight_reps", False, {"weight_kg", "reps", "rir", "is_warmup"}),
        ("reps", False, {"reps", "weight_kg", "rir", "is_warmup"}),
        ("time", False, {"duration_seconds", "weight_kg", "is_warmup"}),
        ("distance_time", False, {"distance_m", "duration_seconds", "is_warmup"}),
        ("time", True, {"duration_seconds", "weight_kg", "side", "is_warmup"}),
    ],
)
def test_set_form_fields(measurement, unilateral, fields):
    form = WorkoutSetForm(measurement=measurement, unilateral=unilateral)

    assert set(form.fields) == fields


@pytest.mark.parametrize(
    "measurement, data, saved",
    [
        ("reps", {"reps": "12"}, {"reps": 12, "weight_kg": Decimal("0")}),
        ("reps", {"reps": "8", "weight_kg": "10"}, {"reps": 8, "weight_kg": Decimal("10")}),
        ("time", {"duration_seconds": "45"}, {"duration_seconds": 45, "reps": None}),
        ("time", {"duration_seconds": "1:30"}, {"duration_seconds": 90}),
        ("distance_time", {"distance_m": "40"}, {"distance_m": 40, "duration_seconds": None}),
    ],
)
def test_set_form_saves_the_right_fields(measurement, data, saved):
    form = WorkoutSetForm(data, measurement=measurement)

    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    for field, value in saved.items():
        assert getattr(instance, field) == value


@pytest.mark.parametrize(
    "measurement, data, error_field",
    [
        ("reps", {}, "reps"),
        ("time", {"duration_seconds": "abc"}, "duration_seconds"),
        ("time", {"duration_seconds": "1:2:3:4"}, "duration_seconds"),
        ("distance_time", {"duration_seconds": "30"}, "distance_m"),
    ],
)
def test_set_form_rejects_missing_or_bad_values(measurement, data, error_field):
    form = WorkoutSetForm(data, measurement=measurement)

    assert not form.is_valid()
    assert error_field in form.errors


def test_one_side_set_needs_a_side():
    form = WorkoutSetForm({"duration_seconds": "20"}, measurement="time", unilateral=True)

    assert not form.is_valid()
    assert "side" in form.errors


# --- the workout screen ------------------------------------------------------


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def core_day(user, plank):
    plan = Plan.objects.create(owner=user, name="Core", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="Core")
    PlanExercise.objects.create(
        day=day, exercise=plank, target_sets=3, hold_min_s=30, hold_max_s=45, rest_seconds=60
    )
    return day


@pytest.mark.django_db
def test_time_card_shows_hold_timer_and_only_time_inputs(logged_in, user, make_workout, core_day):
    workout = make_workout(user, plan_day=core_day, days_ago=0, finished=False)

    content = logged_in.get(reverse("workouts:workout_detail", args=[workout.pk])).content.decode()

    assert "data-hold-timer" in content and "Start hold" in content
    assert "0/3 sets · 30–45 s" in content
    # First time: a test hold, so no seconds are pre-filled (see test_calibration.py).
    assert 'name="duration_seconds"' in content
    assert 'name="reps"' not in content
    assert ">Added kg<" in content


@pytest.mark.django_db
def test_logging_a_hold_with_htmx(logged_in, user, make_workout, core_day, plank):
    workout = make_workout(user, plan_day=core_day, days_ago=0, finished=False)
    url = reverse("workouts:set_create", args=[workout.pk, plank.pk])

    response = logged_in.post(url, {"duration_seconds": "42"}, **HTMX)

    workout_set = WorkoutSet.objects.get()
    assert (workout_set.duration_seconds, workout_set.reps) == (42, None)
    assert json.loads(response["HX-Trigger"])["restStart"]["seconds"] == 60
    assert "42 s" in response.content.decode()


@pytest.mark.django_db
def test_weight_card_has_no_hold_timer(logged_in, user, make_workout, bench):
    workout = make_workout(user, days_ago=0, finished=False)

    content = logged_in.get(
        reverse("workouts:workout_detail", args=[workout.pk]), {"add": bench.pk}
    ).content.decode()

    assert "data-hold-timer" not in content
    assert 'name="weight_kg"' in content and 'name="reps"' in content
    assert 'name="duration_seconds"' not in content


@pytest.mark.django_db
def test_one_side_card_alternates_sides(logged_in, user, make_workout, copenhagen):
    workout = make_workout(user, days_ago=0, finished=False)
    url = reverse("workouts:set_create", args=[workout.pk, copenhagen.pk])

    response = logged_in.post(url, {"duration_seconds": "20", "side": "left"}, **HTMX)

    content = response.content.decode()
    assert "L 20 s" in content
    # The next set is pre-set to the right side.
    assert (
        'value="right" class="side-radio"' in content
        and "checked" in content.split('value="right"')[1].split(">")[0]
    )


@pytest.mark.django_db
def test_old_sets_keep_showing_as_logged_after_a_type_change(logged_in, user, make_workout, plank):
    finished = log(user, make_workout, plank, [{"weight_kg": Decimal("0"), "reps": 60}])

    content = logged_in.get(reverse("workouts:workout_detail", args=[finished.pk])).content.decode()

    assert "0 kg × 60" in content


# --- plan targets per type ---------------------------------------------------


@pytest.mark.django_db
def test_plan_form_for_time_exercise_asks_for_hold_seconds(logged_in, user, plank):
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="P"), name="Core")
    url = f"{reverse('plans:pe_create', args=[day.pk])}?exercise={plank.pk}"

    content = logged_in.get(url).content.decode()
    logged_in.post(url, {"target_sets": 3, "hold_min_s": 30, "hold_max_s": 45, "rest_seconds": 60})

    assert 'name="hold_min_s"' in content and 'name="rep_min"' not in content
    item = day.exercises.get()
    assert (item.hold_min_s, item.hold_max_s, item.target_label) == (30, 45, "30–45 s")


@pytest.mark.django_db
def test_plan_form_rejects_hold_min_above_max(logged_in, user, plank):
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="P"), name="Core")
    url = f"{reverse('plans:pe_create', args=[day.pk])}?exercise={plank.pk}"

    response = logged_in.post(
        url, {"target_sets": 3, "hold_min_s": 60, "hold_max_s": 30, "rest_seconds": 60}
    )

    assert response.context["form"].errors["hold_max_s"]
    assert not day.exercises.exists()


@pytest.mark.django_db
def test_target_labels(user, bench, pull_ups, farmers_walk):
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="P"), name="D")

    def label(exercise, **fields):
        return PlanExercise(day=day, exercise=exercise, **fields).target_label

    assert label(bench, rep_min=8, rep_max=12) == "8–12 reps"
    assert label(pull_ups, rep_min=5, rep_max=5) == "5 reps"
    assert label(farmers_walk, target_distance_m=40) == "40 m"
    assert label(farmers_walk) == ""


# --- seed, import and the data fingerprint ----------------------------------


@pytest.mark.django_db
def test_seed_sets_types_for_originals_and_adds_extra_holds():
    call_command("seed_exercises")

    def kind(name):
        e = Exercise.objects.get(name=name, owner=None)
        return (e.measurement, e.category, e.is_unilateral)

    assert kind("Barbell Bench Press") == ("weight_reps", "strength", False)
    assert kind("Pull-up") == ("reps", "strength", False)
    assert kind("Plank") == ("time", "isometric", False)
    assert kind("Farmer's Walk") == ("distance_time", "strength", False)
    assert kind("Bulgarian Split Squat") == ("weight_reps", "strength", True)
    assert kind("Copenhagen Plank") == ("time", "isometric", True)
    assert kind("Single-Leg Balance") == ("time", "motor", True)
    assert kind("Spanish Squat Hold")[0] == "time"


@pytest.mark.django_db
def test_seed_keeps_ids_of_originals(user, make_workout):
    call_command("seed_exercises")
    plank = Exercise.objects.get(name="Plank", owner=None)
    make_workout(user, {plank: [(0, 60)]})

    call_command("seed_exercises")

    assert Exercise.objects.get(name="Plank", owner=None).pk == plank.pk
    assert WorkoutSet.objects.get().exercise_id == plank.pk


@pytest.mark.parametrize(
    "record, expected",
    [
        ({"id": "x", "name": "Hamstring Stretch", "category": "stretching", "force": "static"},
         ("time", "mobility", False)),
        ({"id": "x", "name": "Side Bridge", "category": "strength", "force": "static",
          "equipment": "body only"}, ("time", "isometric", False)),
        ({"id": "x", "name": "Yoke Walk", "category": "strongman", "force": "push"},
         ("distance_time", "strength", False)),
        ({"id": "Rowing_Stationary", "name": "Rowing, Stationary", "category": "cardio"},
         ("distance_time", "cardio", False)),
        ({"id": "Rope_Jumping", "name": "Rope Jumping", "category": "cardio"},
         ("time", "cardio", False)),
        ({"id": "x", "name": "Box Jump", "category": "plyometrics", "force": "push"},
         ("reps", "plyometric", False)),
        ({"id": "x", "name": "Pushups", "category": "strength", "equipment": "body only"},
         ("reps", "strength", False)),
        ({"id": "x", "name": "One-Arm Dumbbell Row", "category": "strength",
          "equipment": "dumbbell"}, ("weight_reps", "strength", True)),
        ({"id": "x", "name": "Kettlebell One-Legged Deadlift", "category": "strength",
          "equipment": "kettlebells"}, ("weight_reps", "strength", True)),
    ],
)  # fmt: skip
def test_import_type_mapping(record, expected):
    from exercises.free_db import type_fields

    fields = type_fields(record)

    assert (fields["measurement"], fields["category"], fields["is_unilateral"]) == expected


@pytest.mark.django_db
def test_import_does_not_change_types_of_originals():
    from exercises.free_db import import_dataset, load_dataset

    call_command("seed_exercises")
    import_dataset(load_dataset())

    plank = Exercise.objects.get(name="Plank", owner=None)
    pull_up = Exercise.objects.get(name="Pull-up", owner=None)
    assert (plank.measurement, plank.category, plank.source_category) == (
        "time",
        "isometric",
        "strength",
    )
    assert pull_up.measurement == "reps"
    stretch = Exercise.objects.filter(source_category="stretching").first()
    assert (stretch.measurement, stretch.category) == ("time", "mobility")


@pytest.mark.django_db
def test_fingerprint_unchanged_by_seed_and_import(user, make_workout, capsys):
    from exercises.free_db import import_dataset, load_dataset

    call_command("seed_exercises")
    squat = Exercise.objects.get(name="Back Squat", owner=None)
    make_workout(user, {squat: [(100, 5), (102.5, 3)]})
    call_command("data_fingerprint")
    before = capsys.readouterr().out.splitlines()[-1]

    call_command("seed_exercises")
    import_dataset(load_dataset())
    call_command("data_fingerprint")
    after = capsys.readouterr().out.splitlines()[-1]

    assert before.strip() == after.strip()
    assert "WorkoutSet=2" in after


@pytest.mark.django_db
def test_fingerprint_detects_a_changed_set(user, make_workout, bench, capsys):
    make_workout(user, {bench: [(60, 10)]})
    call_command("data_fingerprint")
    before = capsys.readouterr().out

    WorkoutSet.objects.update(reps=9)
    call_command("data_fingerprint")

    assert capsys.readouterr().out != before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fixture, text",
    [
        ("plank", "Hold as long as your form stays good"),
        ("pull_ups", "Do as many clean reps as you can"),
        ("farmers_walk", "Pick a distance"),
        ("bench", "find your working weight, no max test"),
    ],
)
def test_first_time_message_fits_the_type(logged_in, user, make_workout, request, fixture, text):
    exercise = request.getfixturevalue(fixture)
    workout = make_workout(user, days_ago=0, finished=False)

    content = logged_in.get(
        reverse("workouts:workout_detail", args=[workout.pk]), {"add": exercise.pk}
    ).content.decode()

    assert text in content
