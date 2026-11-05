"""Old "0 × 60" sets of time exercises become "60 s" (migration workouts/0004),
and the deploy check (data_fingerprint --compare) allows exactly that change."""

import importlib
from decimal import Decimal

import pytest
from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError

from exercises.models import Exercise
from workouts.management.commands.data_fingerprint import compare, snapshot
from workouts.models import WorkoutSet

migration = importlib.import_module("workouts.migrations.0004_old_time_sets_to_seconds")


@pytest.fixture
def plank(db):
    return Exercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", measurement="time"
    )


@pytest.fixture
def old_sets(user, make_workout, plank, bench):
    """A pre-1.6 workout: plank logged as 0 × seconds, a weighted plank and a bench press."""
    make_workout(user, {plank: [(0, 60), (0, 45), (10, 30)], bench: [(0, 12), (60, 10)]})
    WorkoutSet.objects.create(
        workout=WorkoutSet.objects.first().workout, exercise=plank, order=4, duration_seconds=50
    )
    return {s.pk: s for s in WorkoutSet.objects.all()}


def _convert():
    lines = []
    converted = migration.convert_old_time_sets(apps, report=lines.append)
    return converted, lines


@pytest.mark.django_db
def test_zero_weight_time_sets_become_seconds(old_sets, plank):
    converted, lines = _convert()

    planks = list(WorkoutSet.objects.filter(exercise=plank).order_by("order"))
    assert [(s.weight_kg, s.reps, s.duration_seconds) for s in planks] == [
        (Decimal("0"), None, 60),
        (Decimal("0"), None, 45),
        (Decimal("10"), 30, None),  # with weight: unclear, so left alone
        (Decimal("0"), None, 50),  # already in seconds
    ]
    assert converted == [planks[0].pk, planks[1].pk]
    assert any("0 × 60 -> 60 s" in line for line in lines)
    assert any("left unchanged" in line and "10 × 30" in line for line in lines)
    assert lines[-1].endswith("converted to seconds: 2")


@pytest.mark.django_db
def test_other_exercises_are_never_converted(old_sets, bench):
    _convert()

    bench_sets = WorkoutSet.objects.filter(exercise=bench).order_by("order")
    assert [(s.weight_kg, s.reps, s.duration_seconds) for s in bench_sets] == [
        (Decimal("0"), 12, None),
        (Decimal("60"), 10, None),
    ]


@pytest.mark.django_db
def test_running_twice_changes_nothing_more(old_sets):
    _convert()
    converted, _ = _convert()

    assert converted == []


@pytest.mark.django_db
def test_no_old_sets_means_no_changes(user, make_workout, bench):
    make_workout(user, {bench: [(60, 10)]})
    before = snapshot()

    converted, lines = _convert()

    assert converted == []
    assert lines == ["  old time sets converted to seconds: 0"]
    assert compare(before, snapshot()) == ([], [])


# --- the deploy check -------------------------------------------------------


@pytest.mark.django_db
def test_fingerprint_changes_only_by_the_converted_sets(old_sets):
    before = snapshot()

    converted, _ = _convert()
    expected, unexpected = compare(before, snapshot())

    assert unexpected == []
    assert expected == [
        f"WorkoutSet {converted[0]}: 0 × 60 -> 60 s",
        f"WorkoutSet {converted[1]}: 0 × 45 -> 45 s",
    ]


@pytest.mark.django_db
def test_any_other_change_is_unexpected(old_sets, bench, plank):
    before = snapshot()

    WorkoutSet.objects.filter(exercise=bench, weight_kg=60).update(reps=9)
    WorkoutSet.objects.filter(exercise=plank, reps=60).update(reps=None, duration_seconds=61)
    WorkoutSet.objects.filter(exercise=plank, duration_seconds=50).delete()
    expected, unexpected = compare(before, snapshot())

    assert expected == []
    assert len(unexpected) == 3
    assert sum("changed" in line for line in unexpected) == 2
    assert sum("removed" in line for line in unexpected) == 1


@pytest.mark.django_db
def test_compare_command_fails_the_deploy_on_unexpected_changes(old_sets, tmp_path, capsys):
    path = tmp_path / "before.json"
    call_command("data_fingerprint", save=str(path))

    _convert()
    call_command("data_fingerprint", compare=str(path))
    out = capsys.readouterr().out
    assert out.count("expected change:") == 2
    assert "Only expected changes (2 old time sets now in seconds)." in out

    WorkoutSet.objects.filter(reps=12).update(reps=11)
    with pytest.raises(CommandError):
        call_command("data_fingerprint", compare=str(path))
    assert "UNEXPECTED: WorkoutSet" in capsys.readouterr().out


@pytest.mark.django_db
def test_compare_with_a_new_database_passes(tmp_path, capsys):
    path = tmp_path / "before.json"
    path.write_text("null")

    call_command("data_fingerprint", compare=str(path))

    assert "nothing to compare" in capsys.readouterr().out


@pytest.mark.django_db
def test_built_in_plank_is_converted_even_before_the_seed_sets_its_type(user, make_workout):
    # build.sh runs migrate before seed_exercises, so the type may still be weight × reps.
    plank = Exercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", measurement="weight_reps"
    )
    mine = Exercise.objects.create(
        name="Plank", muscle_group="core", equipment="bodyweight", owner=user
    )
    make_workout(user, {plank: [(0, 40)], mine: [(0, 8)]})

    converted, _ = _convert()

    assert converted == [WorkoutSet.objects.get(exercise=plank).pk]
    assert WorkoutSet.objects.get(exercise=mine).reps == 8
