""" "Change variant": the chooser, the plan editor, the exercise page and the workout
("Only today" / "Change in the plan too"; logged sets stay with their variant)."""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.urls import reverse

from exercises.models import Exercise
from exercises.services import create_variant, ensure_movement
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import WorkoutSet, WorkoutSwap

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def step_up(db):
    exercise = Exercise.objects.create(
        name="Dumbbell Step Ups", muscle_group="quads", equipment="dumbbell",
        primary_muscles=["quadriceps"], instructions=["Step up."],
    )  # fmt: skip
    ensure_movement(exercise)
    return exercise


@pytest.fixture
def smith_step_up(step_up):
    return Exercise.objects.create(
        name="Smith Machine Step-up", muscle_group="quads", equipment="smith",
        movement=step_up.movement,
    )  # fmt: skip


@pytest.fixture
def day(user, step_up):
    plan = Plan.objects.create(owner=user, name="Legs", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="Legs A", order=1)
    PlanExercise.objects.create(
        day=day, exercise=step_up, order=1, target_sets=4, rep_min=10, rep_max=12, rest_seconds=75
    )
    return day


@pytest.fixture
def item(day):
    return day.exercises.get()


@pytest.fixture
def workout(user, make_workout, day):
    return make_workout(user, days_ago=0, finished=False, plan_day=day)


def _chooser(client, exercise, action, back="/"):
    url = reverse("exercises:change_variant", args=[exercise.pk])
    return client.get(url, {"action": action, "back": back})


# --- the chooser -------------------------------------------------------------------


@pytest.mark.django_db
def test_chooser_lists_variants_then_equipment_without_one(logged_in, step_up, smith_step_up):
    content = _chooser(logged_in, step_up, "/somewhere/").content.decode()

    assert content.index("Variants of this movement") < content.index("Other equipment")
    assert "Smith Machine Step-up" in content
    equipment = content[content.index("Other equipment") :]
    # Not in the reviewed list: equipment similar to the family's (dumbbell, Smith).
    for label in ("Barbell", "Kettlebell", "Cable", "Other…"):
        assert label in equipment, label
    for label in ("Pull-up bar", "Resistance band", "Landmine", "TRX / suspension", "Bodyweight"):
        assert label not in equipment, label
    # Smith and dumbbell already exist in the family: not offered again as new.
    assert 'name="equipment" value="smith"' not in content
    assert 'name="equipment" value="dumbbell"' not in content
    assert 'action="/somewhere/"' in content


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["", "https://evil.example/x", "//evil.example/"])
def test_chooser_refuses_foreign_actions(logged_in, step_up, action):
    assert _chooser(logged_in, step_up, action).status_code == 400


@pytest.mark.django_db
def test_chooser_hides_other_users_variants(logged_in, other_user, step_up):
    create_variant(other_user, step_up, "kettlebell")

    content = _chooser(logged_in, step_up, "/x/").content.decode()

    assert "Step Ups (Kettlebell)" not in content
    assert 'name="equipment" value="kettlebell"' in content


# --- exercise page -------------------------------------------------------------------


@pytest.mark.django_db
def test_exercise_page_button_opens_or_creates_the_variant(logged_in, user, step_up):
    page = logged_in.get(reverse("exercises:exercise_detail", args=[step_up.pk]))
    link = page.context["change_variant_url"]
    action = parse_qs(urlsplit(link).query)["action"][0]

    response = logged_in.post(action, {"equipment": "kettlebell"})

    variant = Exercise.objects.get(owner=user, equipment="kettlebell")
    assert variant.name == "Step Ups (Kettlebell)"
    assert variant.movement_id == step_up.movement_id
    assert response.url == reverse("exercises:exercise_detail", args=[variant.pk])


@pytest.mark.django_db
def test_other_equipment_needs_a_name(logged_in, user, step_up):
    action = reverse("exercises:variant_open", args=[step_up.pk])

    assert logged_in.post(action, {"equipment": "other"}).status_code == 404
    logged_in.post(action, {"equipment": "other", "other_name": "weighted vest"})

    assert Exercise.objects.get(owner=user).name == "Step Ups (weighted vest)"


@pytest.mark.django_db
def test_cannot_pick_an_exercise_outside_the_family(logged_in, step_up):
    stranger = Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")

    response = logged_in.post(
        reverse("exercises:variant_open", args=[step_up.pk]), {"exercise": stranger.pk}
    )

    assert response.status_code == 404


# --- plan editor ---------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_editor_changes_the_variant_and_keeps_targets(logged_in, day, item, smith_step_up):
    page = logged_in.get(reverse("plans:plan_detail", args=[day.plan.pk])).content.decode()
    assert "Change variant of Dumbbell Step Ups" in page

    logged_in.post(
        reverse("plans:pe_change_variant", args=[item.pk]), {"exercise": smith_step_up.pk}
    )

    item.refresh_from_db()
    assert item.exercise == smith_step_up
    assert (item.target_sets, item.rep_min, item.rep_max, item.rest_seconds) == (4, 10, 12, 75)


@pytest.mark.django_db
def test_other_users_plan_is_off_limits(client, other_user, item, smith_step_up):
    client.force_login(other_user)

    response = client.post(
        reverse("plans:pe_change_variant", args=[item.pk]), {"exercise": smith_step_up.pk}
    )

    assert response.status_code == 404


# --- workout -------------------------------------------------------------------------


def _change(client, workout, exercise, data):
    return client.post(reverse("workouts:change_variant", args=[workout.pk, exercise.pk]), data)


def _apply(client, workout, item, exercise, scope):
    return client.post(
        reverse("workouts:apply_variant", args=[workout.pk, item.pk]),
        {"exercise": exercise.pk, "scope": scope},
    )


@pytest.mark.django_db
def test_card_has_the_change_variant_button(logged_in, workout, step_up):
    page = logged_in.get(reverse("workouts:workout_detail", args=[workout.pk]))

    link = page.context["cards"][0]["change_variant_url"]
    query = parse_qs(urlsplit(link).query)
    assert query["action"] == [reverse("workouts:change_variant", args=[workout.pk, step_up.pk])]
    assert "Change variant of Dumbbell Step Ups" in page.content.decode()


@pytest.mark.django_db
def test_picking_new_equipment_asks_only_today_or_in_the_plan(logged_in, workout, step_up):
    WorkoutSet.objects.create(workout=workout, exercise=step_up, order=1, weight_kg=10, reps=12)

    response = _change(logged_in, workout, step_up, {"equipment": "kettlebell"})

    content = response.content.decode()
    assert "Only today" in content and "Change in the plan too" in content
    assert "The 1 set you already logged stays with Dumbbell Step Ups." in content
    assert Exercise.objects.get(equipment="kettlebell").name == "Step Ups (Kettlebell)"


@pytest.mark.django_db
def test_only_today(logged_in, user, make_workout, workout, day, item, step_up, smith_step_up):
    WorkoutSet.objects.create(workout=workout, exercise=step_up, order=1, weight_kg=10, reps=12)

    _apply(logged_in, workout, item, smith_step_up, "today")

    item.refresh_from_db()
    assert item.exercise == step_up  # plan unchanged
    assert WorkoutSwap.objects.get().exercise == smith_step_up
    cards = logged_in.get(reverse("workouts:workout_detail", args=[workout.pk])).context["cards"]
    by_exercise = {card["exercise"]: card for card in cards}
    # The plan's slot (targets 4 × 10–12) is now Smith; the logged set stays with dumbbells.
    assert by_exercise[smith_step_up]["plan_exercise"] == item
    assert by_exercise[smith_step_up]["target"] == 4
    assert by_exercise[step_up]["done"] == 1
    assert WorkoutSet.objects.get().exercise == step_up

    # Logging the swapped exercise uses the plan's rest time.
    response = logged_in.post(
        reverse("workouts:set_create", args=[workout.pk, smith_step_up.pk]),
        {"weight_kg": "40", "reps": "10"},
        **HTMX,
    )
    assert '"seconds": 75' in response["HX-Trigger"]

    # Next workout from the same plan day: dumbbells again.
    logged_in.post(reverse("workouts:workout_finish", args=[workout.pk]), {"note": ""})
    nxt = make_workout(user, days_ago=0, finished=False, plan_day=day)
    cards = logged_in.get(reverse("workouts:workout_detail", args=[nxt.pk])).context["cards"]
    assert [card["exercise"] for card in cards] == [step_up]


@pytest.mark.django_db
def test_change_in_the_plan_too(
    logged_in, user, make_workout, workout, day, item, step_up, smith_step_up
):
    WorkoutSet.objects.create(workout=workout, exercise=step_up, order=1, weight_kg=10, reps=12)

    _apply(logged_in, workout, item, smith_step_up, "plan")

    item.refresh_from_db()
    assert item.exercise == smith_step_up
    assert (item.target_sets, item.rep_min, item.rep_max) == (4, 10, 12)
    assert not WorkoutSwap.objects.exists()
    assert WorkoutSet.objects.get().exercise == step_up  # history stays put
    logged_in.post(reverse("workouts:workout_finish", args=[workout.pk]), {"note": ""})
    nxt = make_workout(user, days_ago=0, finished=False, plan_day=day)
    cards = logged_in.get(reverse("workouts:workout_detail", args=[nxt.pk])).context["cards"]
    assert [card["exercise"] for card in cards] == [smith_step_up]


@pytest.mark.django_db
def test_switching_back_today_forgets_the_swap(logged_in, workout, item, step_up, smith_step_up):
    _apply(logged_in, workout, item, smith_step_up, "today")

    _apply(logged_in, workout, item, step_up, "today")

    assert not WorkoutSwap.objects.exists()


@pytest.mark.django_db
def test_extra_exercise_just_shows_the_new_card(
    logged_in, user, make_workout, step_up, smith_step_up
):
    workout = make_workout(user, days_ago=0, finished=False)  # no plan

    response = _change(logged_in, workout, step_up, {"exercise": smith_step_up.pk})

    assert response.url.endswith(f"?add={smith_step_up.pk}#ex-{smith_step_up.pk}")


@pytest.mark.django_db
def test_apply_refuses_exercises_outside_the_family(logged_in, workout, item):
    stranger = Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")

    assert _apply(logged_in, workout, item, stranger, "today").status_code == 404
    assert not WorkoutSwap.objects.exists()


@pytest.mark.django_db
def test_bad_scope_is_refused(logged_in, workout, item, smith_step_up):
    assert _apply(logged_in, workout, item, smith_step_up, "forever").status_code == 404


@pytest.mark.django_db
def test_other_users_workout_is_off_limits(
    client, other_user, workout, item, step_up, smith_step_up
):
    client.force_login(other_user)

    assert _change(client, workout, step_up, {"exercise": smith_step_up.pk}).status_code == 404
    assert _apply(client, workout, item, smith_step_up, "today").status_code == 404


@pytest.mark.django_db
def test_finished_workout_cannot_change(logged_in, user, make_workout, day, item, smith_step_up):
    finished = make_workout(user, days_ago=1, finished=True, plan_day=day)

    assert _apply(logged_in, finished, item, smith_step_up, "today").status_code == 404


# --- which equipment comes first (exercises/variant_equipment.py) -------------------


def _offered(content):
    """Equipment values offered for a new variant ("other" is "Other…")."""
    import re

    return re.findall(r'name="equipment" value="(\w+)"', content)


@pytest.mark.django_db
def test_only_fitting_equipment_is_offered(logged_in, step_up, smith_step_up):
    """Not in the reviewed list: equipment similar to the family's (dumbbell, Smith)."""
    offered = _offered(_chooser(logged_in, step_up, "/x/").content.decode())

    assert offered == ["barbell", "kettlebell", "cable", "other"]  # "Other…" always last


@pytest.mark.django_db
def test_popular_movements_use_the_reviewed_list(logged_in):
    """Hip thrust: barbell, Smith (variants) and a machine; nobody does it with a band."""
    hip_thrust = Exercise.objects.create(
        name="Barbell Hip Thrust", muscle_group="glutes", equipment="barbell"
    )
    ensure_movement(hip_thrust)
    Exercise.objects.create(
        name="Smith Machine Hip Thrust", muscle_group="glutes", equipment="smith",
        movement=hip_thrust.movement,
    )  # fmt: skip

    offered = _offered(_chooser(logged_in, hip_thrust, "/x/").content.decode())

    assert offered == ["machine", "other"]


@pytest.mark.django_db
def test_a_users_own_variant_of_a_popular_movement_uses_its_list(logged_in, user):
    hammer = Exercise.objects.create(
        name="Hammer Curl", muscle_group="biceps", equipment="dumbbell"
    )
    own = create_variant(user, hammer, "cable")

    assert _offered(_chooser(logged_in, own, "/x/").content.decode()) == [
        "kettlebell", "band", "other",
    ]  # fmt: skip


@pytest.mark.django_db
def test_bench_press_offers_no_odd_equipment(logged_in, user):
    """All sensible bench press variants exist: only "Other…" is left, and odd equipment
    can't be chosen by a hand-made request either."""
    from django.core.management import call_command

    call_command("seed_exercises")
    bench = Exercise.objects.get(name="Barbell Bench Press", owner=None)
    content = _chooser(logged_in, bench, "/x/").content.decode()

    assert _offered(content) == ["other"]
    assert "Show all equipment" not in content
    action = reverse("exercises:variant_open", args=[bench.pk])
    for equipment in ("pullup_bar", "kettlebell", "plate", "landmine", "suspension"):
        assert logged_in.post(action, {"equipment": equipment}).status_code == 404, equipment
    assert not Exercise.objects.filter(owner=user).exists()


def test_reviewed_list_names_the_original_exercises():
    from exercises.seed_data import EXERCISES
    from exercises.variant_equipment import SHOWN_EQUIPMENT

    assert set(SHOWN_EQUIPMENT) <= {name for name, *_ in EXERCISES}
