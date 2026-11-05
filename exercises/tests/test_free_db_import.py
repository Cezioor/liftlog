import json
from decimal import Decimal

import pytest
from django.core.management import call_command

from exercises.free_db import (
    IMAGE_BASE_URL,
    LEGACY_MATCHES,
    PENDING_MATCHES,
    equipment_for,
    import_dataset,
    load_dataset,
    muscle_group_for,
    withheld_ids,
)
from exercises.free_db_polish import POLISH_NAMES
from exercises.models import Exercise
from exercises.seed_data import ALIASES, EXERCISES
from exercises.services import search_exercises
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import WorkoutSet


def record(source_id, name, **extra):
    return {
        "id": source_id,
        "name": name,
        "force": "push",
        "level": "beginner",
        "mechanic": "compound",
        "equipment": "barbell",
        "primaryMuscles": ["quadriceps"],
        "secondaryMuscles": ["glutes", "hamstrings"],
        "instructions": ["Step one.", "  ", "Step two."],
        "category": "strength",
        "images": [f"{source_id}/0.jpg", f"{source_id}/1.jpg"],
        **extra,
    }


SAMPLE = [
    # Counterpart of the original "Back Squat".
    record("Barbell_Squat", "Barbell Squat"),
    # Candidate of a pending match ("Dip"): must not be imported yet.
    record("Dips_-_Chest_Version", "Dips - Chest Version", primaryMuscles=["chest"]),
    # New exercise with Polish names.
    record("Sumo_Deadlift", "Sumo Deadlift", primaryMuscles=["hamstrings"], level="expert"),
    # New exercise without photos, equipment or level.
    record("Air_Bike", "Air Bike", equipment=None, level=None, images=[], primaryMuscles=[]),
    # A new id whose name is already used by an original built-in exercise.
    record("Some_Other_Plank", "Plank", equipment="body only"),
]


@pytest.fixture
def originals(db):
    call_command("seed_exercises")
    return dict(Exercise.objects.values_list("name", "pk"))


# --- mapping helpers ------------------------------------------------------


@pytest.mark.parametrize(
    "muscles, category, expected",
    [
        (["quadriceps"], "strength", "quads"),
        (["lats"], "strength", "back"),
        (["traps"], "strength", "back"),
        (["abdominals"], "strength", "core"),
        (["adductors"], "strength", "glutes"),
        (["neck"], "strength", "other"),
        ([], "strength", "other"),
        (["quadriceps"], "olympic weightlifting", "full_body"),
    ],
)
def test_muscle_group_mapping(muscles, category, expected):
    assert muscle_group_for({"primaryMuscles": muscles, "category": category}) == expected


@pytest.mark.parametrize(
    "equipment, expected",
    [
        ("body only", "bodyweight"),
        ("e-z curl bar", "barbell"),
        ("kettlebells", "kettlebell"),
        ("bands", "band"),
        ("medicine ball", "other"),
        (None, "other"),
    ],
)
def test_equipment_mapping(equipment, expected):
    assert equipment_for({"equipment": equipment}) == expected


# --- importing ------------------------------------------------------------


@pytest.mark.django_db
def test_original_exercise_is_enriched_but_keeps_its_own_fields(originals):
    squat_id = originals["Back Squat"]

    import_dataset(SAMPLE)

    squat = Exercise.objects.get(pk=squat_id)
    assert squat.name == "Back Squat"  # not renamed to "Barbell Squat"
    assert squat.aliases == ALIASES["Back Squat"]
    assert squat.progression_step_kg == Decimal("5")
    assert squat.source_id == "Barbell_Squat"
    assert squat.primary_muscles == ["quadriceps"]
    assert squat.secondary_muscles == ["glutes", "hamstrings"]
    assert squat.instructions == ["Step one.", "Step two."]  # empty steps dropped
    assert squat.level == "beginner"
    assert squat.thumbnail_url == f"{IMAGE_BASE_URL}Barbell_Squat/0.jpg"
    assert not Exercise.objects.filter(name="Barbell Squat").exists()


@pytest.mark.django_db
def test_new_exercises_are_created_as_builtins(originals):
    report = import_dataset(SAMPLE)

    sumo = Exercise.objects.get(source_id="Sumo_Deadlift")
    assert sumo.owner is None
    assert (sumo.muscle_group, sumo.equipment, sumo.level) == ("hamstrings", "barbell", "expert")
    assert sumo.aliases == POLISH_NAMES["Sumo_Deadlift"]
    assert sumo.progression_step_kg == Decimal("5")
    bike = Exercise.objects.get(source_id="Air_Bike")
    assert (bike.equipment, bike.level, bike.images, bike.thumbnail_url) == ("other", "", [], "")
    assert report.created == 2


@pytest.mark.django_db
def test_pending_candidates_are_not_imported(originals):
    report = import_dataset(SAMPLE)

    assert not Exercise.objects.filter(source_id="Dips_-_Chest_Version").exists()
    assert report.withheld == 1
    assert Exercise.objects.get(name="Dip").source_id is None  # unchanged


@pytest.mark.django_db
def test_name_clash_with_unmatched_builtin_is_skipped(originals):
    report = import_dataset(SAMPLE)

    assert Exercise.objects.filter(name="Plank").count() == 1
    assert ("Some_Other_Plank", "name “Plank” is taken") in report.conflicts


@pytest.mark.django_db
def test_running_twice_changes_nothing(originals):
    import_dataset(SAMPLE)
    snapshot = list(Exercise.objects.order_by("pk").values())

    report = import_dataset(SAMPLE)

    assert list(Exercise.objects.order_by("pk").values()) == snapshot
    assert (report.created, report.updated) == (0, 2)
    assert Exercise.objects.count() == len(EXERCISES) + 2


@pytest.mark.django_db
def test_plans_and_workouts_keep_pointing_at_the_same_exercise(originals, user, make_workout):
    squat = Exercise.objects.get(name="Back Squat")
    workout = make_workout(user, {squat: [(100, 5), (100, 5)]})
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="P"), name="Legs")
    PlanExercise.objects.create(day=day, exercise=squat)

    import_dataset(SAMPLE)

    assert set(WorkoutSet.objects.values_list("exercise_id", flat=True)) == {squat.pk}
    assert PlanExercise.objects.get().exercise_id == squat.pk
    assert workout.sets.count() == 2


@pytest.mark.django_db
def test_imported_polish_names_are_searchable(originals, user):
    import_dataset(SAMPLE)

    names = [e.name for e in search_exercises(user, "martwy ciag sumo")]

    assert names == ["Sumo Deadlift"]


@pytest.mark.django_db
def test_command_reports_and_checks_workouts(originals, tmp_path, capsys):
    data_file = tmp_path / "exercises.json"
    data_file.write_text(json.dumps(SAMPLE), encoding="utf-8")

    call_command("import_free_exercise_db", file=str(data_file))
    call_command("import_free_exercise_db", file=str(data_file))

    out = capsys.readouterr().out
    assert "2 created" in out and "0 created, 2 updated" in out
    assert "Workouts unchanged: 0 workouts, 0 sets." in out
    assert "Waiting for confirmation: Dip" in out


# --- the real dataset -----------------------------------------------------


def test_reviewed_mapping_matches_the_dataset():
    ids = {r["id"] for r in load_dataset()}
    originals = {name for name, *_ in EXERCISES}

    # Every original is either matched or waiting for confirmation, never both.
    assert set(LEGACY_MATCHES) | set(PENDING_MATCHES) == originals
    assert not set(LEGACY_MATCHES) & set(PENDING_MATCHES)
    # Every id exists and is used at most once.
    assert set(LEGACY_MATCHES.values()) <= ids
    assert len(set(LEGACY_MATCHES.values())) == len(LEGACY_MATCHES)
    assert withheld_ids() <= ids
    assert not withheld_ids() & set(LEGACY_MATCHES.values())
    # Polish names only for imported exercises, ~150 of them.
    assert set(POLISH_NAMES) <= ids - set(LEGACY_MATCHES.values()) - withheld_ids()
    assert len(POLISH_NAMES) >= 150


@pytest.mark.django_db
def test_full_import_of_the_real_dataset(originals):
    data = load_dataset()

    report = import_dataset(data)
    again = import_dataset(data)

    assert len(data) == 876
    assert len(report.legacy_matched) == len(LEGACY_MATCHES)
    assert report.conflicts == [] and report.legacy_missing == []
    assert report.created + len(LEGACY_MATCHES) + report.withheld == len(data)
    assert again.created == 0
    # The originals are all still there, with their ids, and nothing is duplicated.
    assert dict(Exercise.objects.filter(name__in=originals).values_list("name", "pk")) == originals
    assert Exercise.objects.count() == len(EXERCISES) + report.created
