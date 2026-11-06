"""Merging a user's own exercise into the built-in one (exercises/merges.py)."""

from decimal import Decimal

import pytest
from django.core.management import call_command

from exercises.merges import apply_merges
from exercises.models import Exercise
from exercises.services import ensure_movement
from plans.models import Plan, PlanDay, PlanExercise
from workouts.management.commands.data_fingerprint import compare, snapshot
from workouts.models import WorkoutSet, WorkoutSwap


@pytest.fixture
def builtin(db):
    exercise = Exercise.objects.create(
        name="Smith Machine Step-up", muscle_group="quads", equipment="smith", is_unilateral=True
    )
    ensure_movement(exercise)
    return exercise


@pytest.fixture
def own(user, builtin):
    return Exercise.objects.create(
        name="Step Ups (Smith machine)", muscle_group="quads", equipment="smith",
        owner=user, movement=builtin.movement,
    )  # fmt: skip


@pytest.fixture
def history(user, make_workout, own, builtin):
    """Two workouts with the own variant, one also with the built-in, a plan and a swap."""
    first = make_workout(user, {own: [(40, 10), (45, 8, True)]}, days_ago=5)
    second = make_workout(user, {own: [(50, 8)], builtin: [(20, 12)]}, days_ago=2)
    plan = Plan.objects.create(owner=user, name="Legs")
    day = PlanDay.objects.create(plan=plan, name="A", order=1)
    item = PlanExercise.objects.create(day=day, exercise=own, order=1)
    other_item = PlanExercise.objects.create(
        day=day,
        exercise=Exercise.objects.create(name="Plank", muscle_group="core", equipment="bodyweight"),
        order=2,
    )
    open_workout = make_workout(user, days_ago=0, finished=False, plan_day=day)
    WorkoutSwap.objects.create(workout=open_workout, plan_exercise=other_item, exercise=own)
    return {"first": first, "second": second, "item": item}


@pytest.mark.django_db
def test_merge_moves_sets_plan_and_swaps_then_deletes_the_copy(user, own, builtin, history):
    sets_before = list(
        WorkoutSet.objects.filter(exercise=own)
        .order_by("pk")
        .values_list("pk", "workout_id", "order", "weight_kg", "reps", "is_warmup")
    )

    (result,) = apply_merges()

    assert (result.sets, result.plan_entries, result.swaps) == (3, 1, 1)
    assert (result.owner, result.target_name) == ("ania", "Smith Machine Step-up")
    assert not Exercise.objects.filter(pk=own.pk).exists()
    # The same sets, same values, now on the built-in.
    moved = list(
        WorkoutSet.objects.filter(pk__in=[s[0] for s in sets_before])
        .order_by("pk")
        .values_list("pk", "workout_id", "order", "weight_kg", "reps", "is_warmup")
    )
    assert moved == sets_before
    assert set(
        WorkoutSet.objects.filter(pk__in=[s[0] for s in sets_before]).values_list(
            "exercise", flat=True
        )
    ) == {builtin.pk}
    assert WorkoutSet.objects.filter(exercise=builtin).count() == 4  # 3 moved + 1 already there
    history["item"].refresh_from_db()
    assert history["item"].exercise == builtin
    assert WorkoutSwap.objects.get().exercise == builtin


@pytest.mark.django_db
def test_merge_is_idempotent_and_needs_the_built_in(user, own):
    Exercise.objects.filter(owner=None).delete()
    assert apply_merges() == []  # no built-in to merge into: the copy stays
    assert Exercise.objects.filter(pk=own.pk).exists()


@pytest.mark.django_db
def test_merge_runs_once(own, builtin, history):
    apply_merges()

    assert apply_merges() == []


@pytest.mark.django_db
def test_other_exercises_and_users_are_untouched(user, other_user, make_workout, own, builtin):
    keep = Exercise.objects.create(
        name="Step Ups (Kettlebell)", muscle_group="quads", equipment="kettlebell", owner=user
    )
    make_workout(user, {keep: [(16, 10)]})

    apply_merges()

    assert WorkoutSet.objects.get().exercise == keep


@pytest.mark.django_db
def test_command_reports_how_many_sets_moved(own, builtin, history, capsys):
    call_command("merge_exercises")

    out = capsys.readouterr().out
    assert "“Step Ups (Smith machine)” of ania into" in out
    assert "3 sets, 1 plan entries, 1 swaps moved" in out
    assert "Merged exercises: 1 (3 sets moved)." in out


# --- the deploy check ------------------------------------------------------------------


@pytest.mark.django_db
def test_fingerprint_changes_only_by_the_sets_assignment(own, builtin, history):
    before = snapshot()

    apply_merges()
    expected, unexpected = compare(before, snapshot())

    assert unexpected == []
    assert f"Exercise {own.pk} merged into {builtin.pk}" in expected
    reassigned = [line for line in expected if "(merge)" in line]
    assert len([line for line in reassigned if line.startswith("WorkoutSet")]) == 3
    assert len([line for line in reassigned if line.startswith("PlanExercise")]) == 1


@pytest.mark.django_db
def test_fingerprint_catches_anything_else_during_a_merge(own, builtin, history):
    before = snapshot()

    apply_merges()
    WorkoutSet.objects.filter(exercise=builtin, weight_kg=Decimal("50")).update(reps=7)
    expected, unexpected = compare(before, snapshot())

    assert len(unexpected) == 1 and "changed" in unexpected[0]


@pytest.mark.django_db
def test_fingerprint_refuses_a_move_to_another_exercise(user, own, builtin, history):
    before = snapshot()
    elsewhere = Exercise.objects.create(name="Lunge", muscle_group="quads", equipment="barbell")

    WorkoutSet.objects.filter(exercise=own).update(exercise=elsewhere)
    PlanExercise.objects.filter(exercise=own).update(exercise=builtin)
    WorkoutSwap.objects.filter(exercise=own).update(exercise=builtin)
    own.delete()
    expected, unexpected = compare(before, snapshot())

    assert sum("WorkoutSet" in line for line in unexpected) == 3
