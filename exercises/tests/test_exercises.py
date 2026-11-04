import pytest
from django.core.management import call_command
from django.db import IntegrityError
from django.urls import reverse

from exercises.models import Exercise
from exercises.seed_data import EXERCISES


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ania", password="pass")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="bartek", password="pass")


# --- Seed command ---------------------------------------------------------


@pytest.mark.django_db
def test_seed_creates_builtin_exercises():
    call_command("seed_exercises")

    assert Exercise.objects.filter(owner__isnull=True).count() == len(EXERCISES)
    assert len(EXERCISES) >= 60


@pytest.mark.django_db
def test_seed_is_idempotent():
    call_command("seed_exercises")
    call_command("seed_exercises")

    assert Exercise.objects.count() == len(EXERCISES)


def test_seed_data_has_unique_names_and_valid_choices():
    from exercises.models import Equipment, MuscleGroup

    names = [name for name, *_ in EXERCISES]
    assert len(names) == len(set(names))
    for _, muscle_group, equipment, _ in EXERCISES:
        assert muscle_group in MuscleGroup.values
        assert equipment in Equipment.values


# --- Model rules ----------------------------------------------------------


@pytest.mark.django_db
def test_builtin_names_are_unique():
    Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")

    with pytest.raises(IntegrityError):
        Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")


@pytest.mark.django_db
def test_two_users_can_have_exercises_with_the_same_name(user, other_user):
    Exercise.objects.create(name="My Row", muscle_group="back", equipment="other", owner=user)
    Exercise.objects.create(name="My Row", muscle_group="back", equipment="other", owner=other_user)

    assert Exercise.objects.filter(name="My Row").count() == 2


@pytest.mark.django_db
def test_visible_to_returns_builtins_and_own_only(user, other_user):
    builtin = Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")
    mine = Exercise.objects.create(name="Mine", muscle_group="core", equipment="other", owner=user)
    Exercise.objects.create(name="Theirs", muscle_group="core", equipment="other", owner=other_user)

    assert set(Exercise.objects.visible_to(user)) == {builtin, mine}


# --- Views ----------------------------------------------------------------


@pytest.mark.django_db
def test_list_requires_login(client):
    response = client.get(reverse("exercises:exercise_list"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_list_hides_other_users_exercises(client, user, other_user):
    Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")
    Exercise.objects.create(name="Mine", muscle_group="core", equipment="other", owner=user)
    Exercise.objects.create(name="Theirs", muscle_group="core", equipment="other", owner=other_user)
    client.force_login(user)

    response = client.get(reverse("exercises:exercise_list"))

    names = [e.name for e in response.context["exercises"]]
    assert names == ["Mine", "Plank"]
    assert "Theirs" not in response.content.decode()


@pytest.mark.django_db
def test_list_search(client, user):
    call_command("seed_exercises")
    client.force_login(user)

    response = client.get(reverse("exercises:exercise_list"), {"q": "squat"})

    names = [e.name for e in response.context["exercises"]]
    assert "Back Squat" in names
    assert all("squat" in n.lower() for n in names)


@pytest.mark.django_db
def test_create_sets_owner_to_current_user(client, user):
    client.force_login(user)

    response = client.post(
        reverse("exercises:exercise_create"),
        {"name": "Landmine Press", "muscle_group": "shoulders", "equipment": "barbell"},
    )

    assert response.status_code == 302
    exercise = Exercise.objects.get(name="Landmine Press")
    assert exercise.owner == user
    assert exercise.is_bodyweight is False


@pytest.mark.django_db
def test_create_rejects_duplicate_of_builtin(client, user):
    Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight")
    client.force_login(user)

    response = client.post(
        reverse("exercises:exercise_create"),
        {"name": "plank", "muscle_group": "core", "equipment": "bodyweight"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["name"]
    assert Exercise.objects.count() == 1


@pytest.mark.django_db
def test_create_allows_name_used_by_another_user(client, user, other_user):
    Exercise.objects.create(name="My Row", muscle_group="back", equipment="other", owner=other_user)
    client.force_login(user)

    response = client.post(
        reverse("exercises:exercise_create"),
        {"name": "My Row", "muscle_group": "back", "equipment": "other"},
    )

    assert response.status_code == 302
    assert Exercise.objects.filter(name="My Row", owner=user).exists()
