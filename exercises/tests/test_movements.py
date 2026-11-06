"""Movement families: grouping built-ins, the variant_of migration, keeping history."""

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from exercises import movements
from exercises.models import Exercise, Movement
from exercises.movements import group_movements, movement_key, pending_groups
from exercises.services import create_variant
from workouts.management.commands.data_fingerprint import compare, snapshot
from workouts.models import WorkoutSet


def _builtin(name, equipment, muscle_group="quads", unilateral=False, category="strength"):
    return Exercise.objects.create(
        name=name, equipment=equipment, muscle_group=muscle_group,
        is_unilateral=unilateral, category=category,
    )  # fmt: skip


@pytest.mark.parametrize(
    "name, key",
    [
        ("Barbell Step Ups", "step up"),
        ("Dumbbell Step Ups", "step up"),
        ("Smith Machine Step-up", "step up"),
        ("Cable Shrugs", "shrug"),
        ("Back Squat", "back squat"),
    ],
)
def test_movement_key_ignores_equipment_hyphens_and_plurals(name, key):
    assert movement_key(name) == key


@pytest.mark.django_db
def test_exercises_differing_only_by_equipment_become_one_family():
    barbell = _builtin("Barbell Step Ups", "barbell")
    dumbbell = _builtin("Dumbbell Step Ups", "dumbbell")
    other = _builtin("Back Squat", "barbell")

    report = group_movements()

    barbell.refresh_from_db()
    dumbbell.refresh_from_db()
    other.refresh_from_db()
    assert barbell.movement_id == dumbbell.movement_id is not None
    assert barbell.movement.owner is None
    assert other.movement_id is None  # alone: no family needed
    assert (report.families, report.exercises, report.created) == (1, 2, 1)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "second, doubt",
    [
        (dict(name="Dumbbell Row", equipment="dumbbell", unilateral=True), "one side"),
        (dict(name="Dumbbell Row", equipment="dumbbell", muscle_group="biceps"), "muscle"),
        (dict(name="Row", equipment="barbell"), "same equipment"),
        (dict(name="Cable Row", equipment="cable", category="mobility"), "categories"),
    ],
)  # fmt: skip
def test_doubtful_groups_wait_for_confirmation(second, doubt):
    first = _builtin("Barbell Row", "barbell")
    _builtin(**second)

    group_movements()

    first.refresh_from_db()
    assert first.movement_id is None
    (pending,) = pending_groups()
    assert pending.key == "row" and any(doubt in d for d in pending.doubts)


@pytest.mark.django_db
def test_confirmed_doubtful_group_is_applied(monkeypatch):
    monkeypatch.setattr(movements, "CONFIRMED_GROUPS", {"row"})
    barbell = _builtin("Barbell Row", "barbell")
    dumbbell = _builtin("Dumbbell Row", "dumbbell", unilateral=True)

    report = group_movements()

    barbell.refresh_from_db()
    dumbbell.refresh_from_db()
    assert barbell.movement_id == dumbbell.movement_id is not None
    assert report.pending == []


@pytest.mark.django_db
def test_rejected_group_is_never_applied(monkeypatch):
    monkeypatch.setattr(movements, "REJECTED_GROUPS", {"crunch"})
    _builtin("Cable Crunch", "cable", muscle_group="core")
    _builtin("Crunches", "bodyweight", muscle_group="core")

    group_movements()

    assert not Exercise.objects.exclude(movement=None).exists()


@pytest.mark.django_db
def test_hand_made_smith_links_join_families_with_other_names():
    rear = _builtin("Dumbbell Rear Lunge", "dumbbell", unilateral=True)
    smith = _builtin("Smith Machine Reverse Lunge", "smith", unilateral=True)

    group_movements()

    rear.refresh_from_db()
    smith.refresh_from_db()
    assert rear.movement_id == smith.movement_id is not None


@pytest.mark.django_db
def test_grouping_is_idempotent():
    _builtin("Barbell Step Ups", "barbell")
    _builtin("Dumbbell Step Ups", "dumbbell")

    group_movements()
    first = list(Exercise.objects.values_list("pk", "movement_id"))
    report = group_movements()

    assert list(Exercise.objects.values_list("pk", "movement_id")) == first
    assert report.created == 0
    assert Movement.objects.count() == 1


@pytest.mark.django_db
def test_merging_families_keeps_users_variants_and_their_history(user, make_workout):
    barbell = _builtin("Barbell Step Ups", "barbell")
    dumbbell = _builtin("Dumbbell Step Ups", "dumbbell")
    # Before the grouping existed, the user had made a variant of each.
    smith = create_variant(user, barbell, "smith")
    kettlebell = create_variant(user, dumbbell, "kettlebell")
    make_workout(user, {smith: [(40, 10)], kettlebell: [(16, 12)]})
    before = snapshot()

    group_movements()

    family = {
        e.pk for e in Exercise.objects.filter(movement=Exercise.objects.get(pk=barbell.pk).movement)
    }
    assert family == {barbell.pk, dumbbell.pk, smith.pk, kettlebell.pk}
    assert Movement.objects.count() == 1  # the second family was merged away
    assert WorkoutSet.objects.filter(exercise=smith).count() == 1
    assert compare(before, snapshot()) == ([], [])  # users, exercises, sets: unchanged


@pytest.mark.django_db
def test_users_own_exercises_are_never_grouped_with_built_ins(user):
    _builtin("Barbell Curl", "barbell", muscle_group="biceps")
    _builtin("Dumbbell Curl", "dumbbell", muscle_group="biceps")
    mine = Exercise.objects.create(
        name="Cable Curl", equipment="cable", muscle_group="biceps", owner=user
    )

    group_movements()

    mine.refresh_from_db()
    assert mine.movement_id is None


@pytest.mark.django_db
def test_command_lists_pending_groups(capsys):
    _builtin("Barbell Row", "barbell")
    _builtin("Dumbbell Row", "dumbbell", unilateral=True)

    call_command("group_movements", pending=True)

    assert "row: Barbell Row [Barbell], Dumbbell Row [Dumbbell]" in capsys.readouterr().out


# --- migration 0009: variant_of links become families ------------------------------


@pytest.mark.django_db(transaction=True)
def test_existing_variants_and_history_survive_the_migration():
    before_migration = [("exercises", "0008_movements_and_equipment")]
    executor = MigrationExecutor(connection)
    executor.migrate(before_migration)
    old = executor.loader.project_state(before_migration).apps
    User = old.get_model("accounts", "User")
    OldExercise = old.get_model("exercises", "Exercise")
    user = User.objects.create(username="cezary")
    base = OldExercise.objects.create(
        name="Barbell Step Ups", muscle_group="quads", equipment="barbell",
        progression_step_kg=5,
    )  # fmt: skip
    variant = OldExercise.objects.create(
        name="Step Ups (Smith machine)", muscle_group="quads", equipment="smith",
        owner=user, variant_of=base, progression_step_kg=5,
    )  # fmt: skip
    loner = OldExercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", progression_step_kg=2.5
    )

    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())

    base_now = Exercise.objects.get(pk=base.pk)
    variant_now = Exercise.objects.get(pk=variant.pk)
    assert variant_now.movement_id == base_now.movement_id is not None
    assert base_now.movement.owner is None  # family of a built-in is built-in
    assert (variant_now.name, variant_now.owner_id) == ("Step Ups (Smith machine)", user.pk)
    assert Exercise.objects.get(pk=loner.pk).movement_id is None
