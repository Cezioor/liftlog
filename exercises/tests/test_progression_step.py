from decimal import Decimal

import pytest
from django.core.management import call_command
from django.urls import reverse

from exercises.models import Exercise
from exercises.services import default_progression_step


@pytest.mark.parametrize(
    "muscle_group, equipment, expected",
    [
        ("quads", "barbell", Decimal("5")),
        ("hamstrings", "machine", Decimal("5")),
        ("glutes", "barbell", Decimal("5")),
        ("calves", "machine", Decimal("5")),
        ("chest", "barbell", Decimal("2.5")),
        ("back", "cable", Decimal("2.5")),
        ("shoulders", "machine", Decimal("2.5")),
        ("chest", "dumbbell", Decimal("2")),
        # Equipment wins: dumbbells go up in 2 kg steps even for legs.
        ("quads", "dumbbell", Decimal("2")),
    ],
)
def test_default_progression_step(muscle_group, equipment, expected):
    assert default_progression_step(muscle_group, equipment) == expected


@pytest.mark.django_db
def test_save_fills_default_step():
    exercise = Exercise.objects.create(
        name="Leg Press X", muscle_group="quads", equipment="machine"
    )

    exercise.refresh_from_db()
    assert exercise.progression_step_kg == Decimal("5")


@pytest.mark.django_db
def test_save_keeps_explicit_step():
    exercise = Exercise.objects.create(
        name="Micro Bench", muscle_group="chest", equipment="barbell", progression_step_kg=1
    )

    exercise.refresh_from_db()
    assert exercise.progression_step_kg == Decimal("1")


@pytest.mark.django_db
def test_seed_sets_steps_including_overrides():
    call_command("seed_exercises")

    steps = dict(Exercise.objects.values_list("name", "progression_step_kg"))
    assert steps["Back Squat"] == Decimal("5")
    assert steps["Barbell Bench Press"] == Decimal("2.5")
    assert steps["Dumbbell Curl"] == Decimal("2")
    assert steps["Deadlift"] == Decimal("5")  # override: "back" group, but a leg lift


@pytest.mark.django_db
def test_create_with_empty_step_uses_default(client, user):
    client.force_login(user)

    client.post(
        reverse("exercises:exercise_create"),
        {"name": "DB Lunge", "muscle_group": "quads", "equipment": "dumbbell"},
    )

    assert Exercise.objects.get(name="DB Lunge").progression_step_kg == Decimal("2")


@pytest.mark.django_db
def test_create_with_custom_step_accepts_comma(client, user):
    client.force_login(user)

    client.post(
        reverse("exercises:exercise_create"),
        {
            "name": "Cable Fly",
            "muscle_group": "chest",
            "equipment": "cable",
            "progression_step_kg": "1,25",
        },
    )

    assert Exercise.objects.get(name="Cable Fly").progression_step_kg == Decimal("1.25")


@pytest.mark.django_db
def test_edit_own_exercise_step(client, user):
    exercise = Exercise.objects.create(
        name="My Press", muscle_group="shoulders", equipment="barbell", owner=user
    )
    client.force_login(user)

    response = client.post(
        reverse("exercises:exercise_update", args=[exercise.pk]),
        {
            "name": "My Press",
            "muscle_group": "shoulders",
            "equipment": "barbell",
            "progression_step_kg": "1",
        },
    )

    assert response.status_code == 302
    exercise.refresh_from_db()
    assert exercise.progression_step_kg == Decimal("1")


@pytest.mark.django_db
def test_step_must_be_positive(client, user):
    client.force_login(user)

    response = client.post(
        reverse("exercises:exercise_create"),
        {"name": "Zero", "muscle_group": "chest", "equipment": "cable", "progression_step_kg": "0"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["progression_step_kg"]


@pytest.mark.django_db
def test_cannot_edit_builtin_or_other_users_exercise(client, user, other_user, bench):
    theirs = Exercise.objects.create(
        name="Their Row", muscle_group="back", equipment="cable", owner=other_user
    )
    client.force_login(user)

    for exercise in (bench, theirs):
        response = client.post(
            reverse("exercises:exercise_update", args=[exercise.pk]),
            {"name": "Hacked", "muscle_group": "chest", "equipment": "cable"},
        )
        assert response.status_code == 404
    assert not Exercise.objects.filter(name="Hacked").exists()
