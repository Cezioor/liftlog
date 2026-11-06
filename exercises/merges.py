"""Merging users' own exercises into a built-in one that is the same exercise.

Used when someone made their own variant before the library had it (e.g. their
"Step Ups (Smith machine)" vs the built-in "Smith Machine Step-up"). Every logged set,
plan entry and "only today" swap moves to the built-in; the own copy is then deleted.
Only `exercise` references change: weights, reps, dates and set order stay exactly as
they were, which `data_fingerprint --compare` checks on deploy.

Runs from build.sh (`merge_exercises`); idempotent: once merged, nothing is left to merge.
"""

from dataclasses import dataclass

from django.db import transaction

from .models import Exercise

# (name of the users' own exercise, name of the built-in it is merged into)
EXERCISE_MERGES = [
    # Decided by the owner on 2026-11-06.
    ("Step Ups (Smith machine)", "Smith Machine Step-up"),
]


@dataclass(frozen=True)
class MergeResult:
    source_id: int
    source_name: str
    owner: str
    target_id: int
    target_name: str
    sets: int
    plan_entries: int
    swaps: int


@transaction.atomic
def merge_into(source, target):
    """Move everything that points at `source` (a user's exercise) to `target`."""
    from plans.models import PlanExercise
    from workouts.models import WorkoutSet, WorkoutSwap

    sets = WorkoutSet.objects.filter(exercise=source).update(exercise=target)
    plan_entries = PlanExercise.objects.filter(exercise=source).update(exercise=target)
    swaps = WorkoutSwap.objects.filter(exercise=source).update(exercise=target)
    # A swap that now points at the plan's own exercise means nothing any more.
    WorkoutSwap.objects.filter(exercise=target, plan_exercise__exercise=target).delete()
    result = MergeResult(
        source.pk, source.name, source.owner.username, target.pk, target.name,
        sets, plan_entries, swaps,
    )  # fmt: skip
    source.delete()
    return result


def apply_merges(merges=None):
    """Merge every user's exercise named like a source into its built-in target."""
    results = []
    for source_name, target_name in merges or EXERCISE_MERGES:
        target = Exercise.objects.filter(owner=None, name=target_name).first()
        if target is None:
            continue  # the built-in doesn't exist (yet): nothing to merge into
        for source in Exercise.objects.filter(owner__isnull=False, name=source_name):
            results.append(merge_into(source, target))
    return results


def merged_ids(before_exercises, after_exercises):
    """{merged-away exercise id: built-in id} between two data_fingerprint snapshots.

    An own exercise counts as merged when it existed before, is gone after, and its
    name is a source in EXERCISE_MERGES whose built-in target exists.
    """
    targets = dict(EXERCISE_MERGES)
    ids = {}
    for key, row in before_exercises.items():
        name = row[2]  # columns: id, owner_id, name, equipment, measurement
        if key in after_exercises or name not in targets:
            continue
        target = (
            Exercise.objects.filter(owner=None, name=targets[name])
            .values_list("pk", flat=True)
            .first()
        )
        if target is not None:
            ids[int(key)] = target
    return ids
