"""Originals whose free-exercise-db match was another exercise (2026-11-14).

Cable Lateral Raise moves from Cable_Seated_Lateral_Raise (seated bent-over, rear delts) to
Standing_Low-Pulley_Deltoid_Raise; the built-in that held that source is folded into it.
Walking Lunge only borrows the photos of Dumbbell_Lunges (a lunge in place), which becomes
a built-in of its own.
"""

from decimal import Decimal

import pytest
from django.core.management import call_command

from exercises.free_db import ORIGINAL_INSTRUCTIONS, import_dataset
from exercises.models import Exercise
from exercises.services import create_variant, ensure_movement
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import WorkoutSet, WorkoutSwap
from workouts.services import progression_hint

from .test_free_db_import import record

RECORDS = [
    record("Standing_Low-Pulley_Deltoid_Raise", "Standing Low-Pulley Deltoid Raise",
           equipment="cable", primaryMuscles=["shoulders"]),
    record("Cable_Seated_Lateral_Raise", "Cable Seated Lateral Raise",
           equipment="cable", primaryMuscles=["shoulders"]),
    record("Dumbbell_Lunges", "Dumbbell Lunges", equipment="dumbbell"),
    record("Barbell_Lunge", "Barbell Lunge"),
    record("Seated_Bent-Over_Rear_Delt_Raise", "Seated Bent-Over Rear Delt Raise",
           equipment="dumbbell", primaryMuscles=["shoulders"]),
]  # fmt: skip


@pytest.fixture
def before_the_switch(db, user, make_workout):
    """The library as it was: our exercise on the old source, the new one a separate built-in."""
    call_command("seed_exercises")
    ours = Exercise.objects.get(owner=None, name="Cable Lateral Raise")
    ours.source_id = "Cable_Seated_Lateral_Raise"
    ours.save()
    lunge = Exercise.objects.get(owner=None, name="Walking Lunge")
    lunge.source_id = "Dumbbell_Lunges"
    lunge.save()
    holder = Exercise.objects.create(
        name="Standing Low-Pulley Deltoid Raise", muscle_group="shoulders", equipment="cable",
        source_id="Standing_Low-Pulley_Deltoid_Raise",
    )  # fmt: skip
    # Someone used it: sets, a plan entry, an "only today" swap and an own variant.
    plan = Plan.objects.create(owner=user, name="Shoulders", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="A", order=1)
    entry = PlanExercise.objects.create(day=day, exercise=holder, order=1)
    plank_entry = PlanExercise.objects.create(
        day=day, exercise=Exercise.objects.get(owner=None, name="Plank"), order=2
    )
    workout = make_workout(user, {holder: [(5, 12), (5, 10)]})
    WorkoutSwap.objects.create(workout=workout, plan_exercise=plank_entry, exercise=holder)
    variant = create_variant(user, holder, "band")
    return {"ours": ours, "holder": holder, "entry": entry, "variant": variant}


@pytest.mark.django_db
def test_the_built_in_on_the_new_source_is_folded_into_ours(before_the_switch):
    ours, holder = before_the_switch["ours"], before_the_switch["holder"]

    report = import_dataset(RECORDS)

    assert not Exercise.objects.filter(pk=holder.pk).exists()
    ours.refresh_from_db()
    assert ours.name == "Cable Lateral Raise"  # same id, name and Polish names
    assert ours.source_id == "Standing_Low-Pulley_Deltoid_Raise"
    assert ours.images[0] == "Standing_Low-Pulley_Deltoid_Raise/0.jpg"
    assert "wznosy bokiem jednorącz na dolnym wyciągu" in ours.aliases
    assert WorkoutSet.objects.filter(exercise=ours).count() == 2
    assert PlanExercise.objects.get(pk=before_the_switch["entry"].pk).exercise == ours
    assert WorkoutSwap.objects.get().exercise == ours
    variant = Exercise.objects.get(pk=before_the_switch["variant"].pk)
    assert variant.movement_id == ours.movement_id
    assert [(r.source_name, r.sets, r.plan_entries, r.swaps) for r in report.folded] == [
        ("Standing Low-Pulley Deltoid Raise", 2, 1, 1)
    ]


@pytest.mark.django_db
def test_the_switch_runs_once(before_the_switch):
    import_dataset(RECORDS)
    second = import_dataset(RECORDS)

    assert second.folded == [] and second.created == 0 and second.conflicts == []
    assert Exercise.objects.filter(source_id="Standing_Low-Pulley_Deltoid_Raise").count() == 1


@pytest.mark.django_db
def test_the_old_sources_become_built_ins_of_their_own(before_the_switch):
    import_dataset(RECORDS)
    call_command("group_movements")

    seated = Exercise.objects.get(source_id="Cable_Seated_Lateral_Raise")
    assert (seated.owner, seated.name) == (None, "Cable Seated Lateral Raise")
    assert seated.aliases.startswith("odwrotne rozpiętki na wyciągu siedząc")
    assert seated.movement == Exercise.objects.get(owner=None, name="Rear Delt Fly").movement

    in_place = Exercise.objects.get(source_id="Dumbbell_Lunges")
    assert (in_place.owner, in_place.name) == (None, "Dumbbell Lunges")
    assert in_place.aliases.startswith("wykroki z hantlami")
    barbell_lunge = Exercise.objects.get(source_id="Barbell_Lunge")
    assert in_place.movement_id == barbell_lunge.movement_id is not None


@pytest.mark.django_db
def test_walking_lunge_keeps_the_photos_with_its_own_instructions(before_the_switch):
    import_dataset(RECORDS)

    lunge = Exercise.objects.get(owner=None, name="Walking Lunge")
    assert lunge.source_id is None  # Dumbbell_Lunges is the built-in "Dumbbell Lunges" now
    assert lunge.images[0] == "Dumbbell_Lunges/0.jpg"
    assert lunge.instructions == ORIGINAL_INSTRUCTIONS["Walking Lunge"]
    assert "photos show the same lunge done in place" in lunge.photo_note
    assert not any("photos" in step for step in lunge.instructions)
    assert "wykroki z hantlami" not in lunge.aliases.split(", ")


@pytest.mark.django_db
def test_cable_lateral_raise_is_one_arm(db):
    call_command("seed_exercises")

    assert Exercise.objects.get(owner=None, name="Cable Lateral Raise").is_unilateral


def test_the_hint_works_when_older_sets_have_no_side():
    """Sets logged before the exercise became one-arm have side "" ."""
    exercise = Exercise(
        name="Cable Lateral Raise", muscle_group="shoulders", equipment="cable",
        measurement="weight_reps", is_unilateral=True, progression_step_kg=Decimal("2.5"),
    )  # fmt: skip
    old = [WorkoutSet(order=n, weight_kg=Decimal("10"), reps=12, side="") for n in (1, 2, 3)]

    hint = progression_hint(exercise, old, rep_min=10, rep_max=12)

    assert hint is not None and hint.increase
    assert hint.weight_kg == Decimal("12.5")


@pytest.mark.django_db
def test_merging_a_family_member_keeps_the_family_together(user):
    """merge_into on a built-in with a family moves the family's other members along."""
    from exercises.merges import merge_into

    target = Exercise.objects.create(name="Target", muscle_group="core", equipment="cable")
    source = Exercise.objects.create(name="Source", muscle_group="core", equipment="cable")
    ensure_movement(source)
    mine = create_variant(user, source, "band")

    result = merge_into(source, target)

    assert result.owner == "built-in"
    mine.refresh_from_db()
    target.refresh_from_db()
    assert mine.movement_id == target.movement_id is not None
