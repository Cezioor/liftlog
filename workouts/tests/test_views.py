import json
from decimal import Decimal

import pytest
from django.urls import reverse

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import Workout, WorkoutSet

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def push_day(user, bench):
    plan = Plan.objects.create(owner=user, name="PPL", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="Push", order=1)
    PlanExercise.objects.create(
        day=day, exercise=bench, order=1, target_sets=3, rep_min=8, rep_max=12, rest_seconds=120
    )
    return day


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def workout(user, push_day, make_workout):
    return make_workout(user, plan_day=push_day, days_ago=0, finished=False)


def _add_set(client, workout, exercise, weight="60", reps="10", **extra):
    url = reverse("workouts:set_create", args=[workout.pk, exercise.pk])
    return client.post(url, {"weight_kg": weight, "reps": reps}, **extra)


# --- starting -------------------------------------------------------------


@pytest.mark.django_db
def test_home_shows_active_plan_days(logged_in, push_day):
    response = logged_in.get(reverse("home"))

    assert "Push" in response.content.decode()


@pytest.mark.django_db
def test_start_workout_from_plan_day(logged_in, user, push_day):
    response = logged_in.post(reverse("workouts:workout_start"), {"plan_day": push_day.pk})

    workout = Workout.objects.get()
    assert response.url == reverse("workouts:workout_detail", args=[workout.pk])
    assert workout.owner == user
    assert workout.plan_day == push_day
    assert workout.finished_at is None


@pytest.mark.django_db
def test_start_empty_workout(logged_in):
    logged_in.post(reverse("workouts:workout_start"))

    assert Workout.objects.get().plan_day is None


@pytest.mark.django_db
def test_start_while_one_is_open_resumes_it(logged_in, workout):
    response = logged_in.post(reverse("workouts:workout_start"))

    assert response.url == reverse("workouts:workout_detail", args=[workout.pk])
    assert Workout.objects.count() == 1


# --- the workout screen ---------------------------------------------------


@pytest.mark.django_db
def test_workout_page_shows_last_time_and_hint(logged_in, user, bench, push_day, make_workout):
    make_workout(user, {bench: [(60, 12), (60, 12), (60, 12)]}, days_ago=3)
    current = make_workout(user, plan_day=push_day, days_ago=0, finished=False)

    response = logged_in.get(reverse("workouts:workout_detail", args=[current.pk]))

    content = response.content.decode()
    assert "60 × 12" in content  # last time, per set
    assert "Try 62.5 kg" in content  # progression hint
    assert 'value="62.5"' in content  # pre-filled weight
    assert 'value="8"' in content  # reps start at bottom of range after an increase
    assert "0/3 sets" in content


@pytest.mark.django_db
def test_add_set_with_htmx_returns_card_and_starts_rest_timer(logged_in, workout, bench):
    response = _add_set(logged_in, workout, bench, "62,5", "9", **HTMX)

    assert response.status_code == 200
    assert response.templates[0].name == "workouts/partials/exercise_card.html"
    assert json.loads(response["HX-Trigger"]) == {"restStart": {"seconds": 120}}
    workout_set = WorkoutSet.objects.get()
    assert (workout_set.weight_kg, workout_set.reps, workout_set.order) == (Decimal("62.5"), 9, 1)
    content = response.content.decode()
    assert "1/3 sets" in content
    assert "Log set 2" in content


@pytest.mark.django_db
def test_add_set_without_htmx_redirects_back(logged_in, workout, bench):
    response = _add_set(logged_in, workout, bench)

    assert response.status_code == 302
    assert response.url.endswith(f"#ex-{bench.pk}")
    assert WorkoutSet.objects.count() == 1


@pytest.mark.django_db
def test_sets_are_numbered_per_exercise(logged_in, workout, bench, squat):
    _add_set(logged_in, workout, bench)
    _add_set(logged_in, workout, squat, "100", "5")
    _add_set(logged_in, workout, bench)

    assert list(workout.sets.filter(exercise=bench).values_list("order", flat=True)) == [1, 2]
    assert workout.sets.get(exercise=squat).order == 1


@pytest.mark.django_db
def test_invalid_set_shows_errors_and_saves_nothing(logged_in, workout, bench):
    response = _add_set(logged_in, workout, bench, "abc", "0", **HTMX)

    assert response.status_code == 200
    assert "HX-Trigger" not in response
    assert "errorlist" in response.content.decode()
    assert not WorkoutSet.objects.exists()


@pytest.mark.django_db
def test_edit_set(logged_in, workout, bench):
    _add_set(logged_in, workout, bench)
    workout_set = WorkoutSet.objects.get()
    url = reverse("workouts:set_update", args=[workout_set.pk])

    assert "Save set 1" in logged_in.get(url, **HTMX).content.decode()
    logged_in.post(url, {"weight_kg": "65", "reps": "8"}, **HTMX)

    workout_set.refresh_from_db()
    assert (workout_set.weight_kg, workout_set.reps) == (Decimal("65"), 8)


@pytest.mark.django_db
def test_delete_set_renumbers_the_rest(logged_in, workout, bench):
    for reps in ("10", "9", "8"):
        _add_set(logged_in, workout, bench, reps=reps)
    first = workout.sets.get(order=1)

    logged_in.post(reverse("workouts:set_delete", args=[first.pk]), **HTMX)

    assert list(workout.sets.values_list("order", "reps")) == [(1, 9), (2, 8)]


@pytest.mark.django_db
def test_extra_exercise_added_during_workout_appears(logged_in, workout, squat):
    url = reverse("workouts:workout_detail", args=[workout.pk])

    assert "Back Squat" in logged_in.get(url, {"add": squat.pk}).content.decode()
    _add_set(logged_in, workout, squat, "100", "5")
    # Once a set is logged, the card stays without the ?add parameter.
    assert "Back Squat" in logged_in.get(url).content.decode()


@pytest.mark.django_db
def test_finish_workout(logged_in, workout, bench):
    _add_set(logged_in, workout, bench)

    response = logged_in.post(
        reverse("workouts:workout_finish", args=[workout.pk]), {"note": "Felt strong"}
    )

    workout.refresh_from_db()
    assert workout.finished_at is not None
    assert workout.note == "Felt strong"
    summary = logged_in.get(response.url).content.decode()
    assert "Felt strong" in summary
    assert "60 kg × 10" in summary


@pytest.mark.django_db
def test_finished_workout_rejects_new_sets(logged_in, user, bench, make_workout):
    finished = make_workout(user, {bench: [(60, 10)]})

    response = _add_set(logged_in, finished, bench)

    assert response.status_code == 404
    assert finished.sets.count() == 1


@pytest.mark.django_db
def test_finished_workout_becomes_last_time_for_next_one(logged_in, workout, bench, push_day):
    _add_set(logged_in, workout, bench, "60", "12")
    logged_in.post(reverse("workouts:workout_finish", args=[workout.pk]))
    logged_in.post(reverse("workouts:workout_start"), {"plan_day": push_day.pk})
    new = Workout.objects.get(finished_at__isnull=True)

    content = logged_in.get(reverse("workouts:workout_detail", args=[new.pk])).content.decode()

    assert "60 × 12" in content


@pytest.mark.django_db
def test_discard_workout(logged_in, workout, bench):
    _add_set(logged_in, workout, bench)

    logged_in.post(reverse("workouts:workout_discard", args=[workout.pk]))

    assert not Workout.objects.exists()
    assert not WorkoutSet.objects.exists()


# --- other users' data ----------------------------------------------------


@pytest.mark.django_db
def test_other_user_cannot_see_or_change_my_workout(client, other_user, workout, bench):
    WorkoutSet.objects.create(workout=workout, exercise=bench, weight_kg=60, reps=10)
    workout_set = workout.sets.get()
    client.force_login(other_user)

    assert client.get(reverse("workouts:workout_detail", args=[workout.pk])).status_code == 404
    assert _add_set(client, workout, bench).status_code == 404
    edit = client.post(
        reverse("workouts:set_update", args=[workout_set.pk]), {"weight_kg": "1", "reps": "1"}
    )
    assert edit.status_code == 404
    assert client.post(reverse("workouts:set_delete", args=[workout_set.pk])).status_code == 404
    assert client.post(reverse("workouts:workout_finish", args=[workout.pk])).status_code == 404
    assert client.post(reverse("workouts:workout_discard", args=[workout.pk])).status_code == 404

    workout_set.refresh_from_db()
    assert workout_set.weight_kg == 60
    workout.refresh_from_db()
    assert workout.finished_at is None


@pytest.mark.django_db
def test_cannot_start_workout_from_another_users_plan_day(client, other_user, push_day):
    client.force_login(other_user)

    response = client.post(reverse("workouts:workout_start"), {"plan_day": push_day.pk})

    assert response.status_code == 404
    assert not Workout.objects.exists()


@pytest.mark.django_db
def test_cannot_log_another_users_private_exercise(logged_in, workout, other_user):
    private = Exercise.objects.create(
        name="Their move", muscle_group="core", equipment="other", owner=other_user
    )

    assert _add_set(logged_in, workout, private).status_code == 404


@pytest.mark.django_db
def test_last_time_never_uses_other_users_history(
    logged_in, other_user, bench, workout, make_workout
):
    make_workout(other_user, {bench: [(140, 3)]})

    content = logged_in.get(reverse("workouts:workout_detail", args=[workout.pk])).content.decode()

    assert "140" not in content
