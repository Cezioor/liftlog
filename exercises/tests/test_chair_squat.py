"""free-exercise-db's Chair Squat is our Smith Machine Hack Squat (owner, 2026-11-15).

The import no longer creates it; `seed_smith_variants` folds a copy left by older imports
into the Smith variant, which keeps its own name and steps and takes the record's photos.
"""

import pytest
from django.core.management import call_command

from exercises.free_db import import_dataset, load_dataset
from exercises.models import Exercise
from exercises.services import create_variant, search_exercises
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import WorkoutSet, WorkoutSwap


@pytest.fixture
def library(db):
    call_command("seed_exercises")
    import_dataset(load_dataset())
    call_command("seed_smith_variants")
    call_command("group_movements")


def test_chair_squat_is_not_a_built_in_of_its_own(library):
    assert not Exercise.objects.filter(name__iexact="Chair Squat").exists()
    assert not Exercise.objects.filter(source_id="Chair_Squat").exists()
    hack = Exercise.objects.get(owner=None, name="Smith Machine Hack Squat")
    assert hack.source_id is None
    assert hack.images == ["Chair_Squat/0.jpg", "Chair_Squat/1.jpg"]
    assert (hack.photo_note, hack.photo_note_pl) == ("", "")
    assert hack.movement == Exercise.objects.get(owner=None, name="Barbell Hack Squat").movement


@pytest.mark.parametrize("query", ["chair squat", "przysiad na smithie ze stopami z przodu"])
def test_chair_squat_finds_the_smith_hack_squat(library, user, query):
    names = [e.name for e in search_exercises(user, query)]
    assert names[0] == "Smith Machine Hack Squat"
    assert "Chair Squat" not in names


@pytest.mark.django_db
def test_an_old_chair_squat_is_folded_into_the_smith_hack_squat(library, user, make_workout):
    hack = Exercise.objects.get(owner=None, name="Smith Machine Hack Squat")
    # The library as it was: Chair Squat a built-in of its own, in the same family.
    old = Exercise.objects.create(
        name="Chair Squat", muscle_group="quads", equipment="smith", source_id="Chair_Squat",
        movement=hack.movement,
    )  # fmt: skip
    plan = Plan.objects.create(owner=user, name="Legs", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="A", order=1)
    entry = PlanExercise.objects.create(day=day, exercise=old, order=1)
    plank_entry = PlanExercise.objects.create(
        day=day, exercise=Exercise.objects.get(owner=None, name="Plank"), order=2
    )
    workout = make_workout(user, {old: [(40, 10), (40, 8)]})
    WorkoutSwap.objects.create(workout=workout, plan_exercise=plank_entry, exercise=old)
    variant = create_variant(user, old, "barbell")

    call_command("seed_smith_variants")
    call_command("seed_smith_variants")  # nothing left to fold the second time

    assert not Exercise.objects.filter(pk=old.pk).exists()
    assert WorkoutSet.objects.filter(exercise=hack).count() == 2
    assert PlanExercise.objects.get(pk=entry.pk).exercise == hack
    assert WorkoutSwap.objects.get().exercise == hack
    variant.refresh_from_db()
    assert variant.movement_id == hack.movement_id
    hack.refresh_from_db()
    assert hack.name == "Smith Machine Hack Squat"
    assert "chair squat" in hack.aliases
