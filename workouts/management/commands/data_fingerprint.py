"""Fingerprint of the user's data: accounts, workouts, sets and plans.

build.sh uses it to prove a deploy left existing data untouched:

    python manage.py data_fingerprint --save snapshot.json     # before the migrations
    python manage.py data_fingerprint --compare snapshot.json  # after migrate/seed/import

`--compare` lists every row that changed and fails unless each change is an expected one.
The only expected change so far is migration workouts/0004: an old time set "0 × 60"
becoming "60 s" (reps moved into duration_seconds). Rows added or removed always fail.

Only columns that existed before Stage 1.6 are snapshotted, so the command also works on a
database whose migrations haven't run yet.
"""

import hashlib
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import Workout, WorkoutSet

FIELDS = {
    # Accounts (no password hashes): proves e.g. the email-verification migration
    # (accounts/0004) added allauth addresses without touching the users themselves.
    get_user_model(): ["id", "username", "email", "is_active", "is_staff", "date_joined"],
    # Users' own exercises (incl. their variants); built-ins are rewritten by every import.
    Exercise: ["id", "owner_id", "name", "equipment", "measurement"],
    Workout: ["id", "owner_id", "plan_day_id", "started_at", "finished_at", "note"],
    WorkoutSet: ["id", "workout_id", "exercise_id", "order", "weight_kg", "reps", "is_warmup"],
    Plan: ["id", "owner_id", "name", "is_active"],
    PlanDay: ["id", "plan_id", "name", "order"],
    PlanExercise: [
        "id",
        "day_id",
        "exercise_id",
        "order",
        "target_sets",
        "rep_min",
        "rep_max",
        "rest_seconds",
    ],
}


def _normalise(value):
    # Decimal('60.00') and Decimal('60') must compare the same; JSON-friendly values.
    if hasattr(value, "normalize"):
        return format(value.normalize(), "f")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def snapshot():
    """{model name: {id: [column values]}} of every fingerprinted row."""
    data = {}
    for model, fields in FIELDS.items():
        rows = model.objects.order_by("pk").values_list(*fields)
        if model is Exercise:
            rows = rows.filter(owner__isnull=False)
        data[model.__name__] = {
            str(row[0]): [_normalise(v) for v in row] for row in rows.iterator(chunk_size=2000)
        }
    return data


def summary(data):
    """One line: row counts plus a short SHA-256 of all rows."""
    digest = hashlib.sha256()
    counts = []
    for name, rows in data.items():
        for key in sorted(rows, key=int):
            digest.update(repr(tuple(rows[key])).encode())
        counts.append(f"{name}={len(rows)}")
    return " ".join(counts) + " sha256=" + digest.hexdigest()[:16]


def fingerprint():
    return summary(snapshot())


def _is_time_conversion(before_row, after_row, duration_seconds):
    """Migration 0004: same set, reps N -> empty, duration_seconds = N, no weight."""
    columns = FIELDS[WorkoutSet]
    before = dict(zip(columns, before_row, strict=True))
    after = dict(zip(columns, after_row, strict=True))
    unchanged = all(before[c] == after[c] for c in columns if c != "reps")
    return (
        unchanged
        and before["weight_kg"] == "0"
        and before["reps"] is not None
        and after["reps"] is None
        and duration_seconds == before["reps"]
    )


def compare(before, after):
    """(expected changes, unexpected changes) between two snapshots, as readable lines."""
    expected, unexpected = [], []
    for name, old_rows in before.items():
        new_rows = after.get(name, {})
        for key in sorted(old_rows.keys() - new_rows.keys(), key=int):
            unexpected.append(f"{name} {key} removed")
        for key in sorted(new_rows.keys() - old_rows.keys(), key=int):
            unexpected.append(f"{name} {key} added")
        changed = [k for k in old_rows.keys() & new_rows.keys() if old_rows[k] != new_rows[k]]
        durations = {}
        if name == "WorkoutSet" and changed:
            durations = dict(
                WorkoutSet.objects.filter(pk__in=[int(k) for k in changed]).values_list(
                    "pk", "duration_seconds"
                )
            )
        for key in sorted(changed, key=int):
            old, new = old_rows[key], new_rows[key]
            if name == "WorkoutSet" and _is_time_conversion(old, new, durations.get(int(key))):
                expected.append(f"WorkoutSet {key}: 0 × {old[5]} -> {old[5]} s")
            else:
                unexpected.append(f"{name} {key} changed: {old} -> {new}")
    return expected, unexpected


class Command(BaseCommand):
    help = "Print a fingerprint of workouts, sets and plans (to prove a deploy changed nothing)."

    def add_arguments(self, parser):
        parser.add_argument("--save", metavar="FILE", help="Also save the rows to FILE.")
        parser.add_argument(
            "--compare", metavar="FILE", help="Compare with rows saved earlier by --save."
        )

    def handle(self, *args, save=None, compare=None, **options):
        try:
            data = snapshot()
        except DatabaseError:
            # Brand-new database: the tables don't exist yet.
            self.stdout.write("empty")
            if save:
                Path(save).write_text("null")
            return
        self.stdout.write(summary(data))

        if save:
            Path(save).write_text(json.dumps(data))
        if compare:
            self._compare(json.loads(Path(compare).read_text()), data)

    def _compare(self, before, after):
        if before is None:
            self.stdout.write("New database: nothing to compare.")
            return
        expected, unexpected = compare(before, after)
        for line in expected:
            self.stdout.write(f"  expected change: {line}")
        for line in unexpected:
            self.stdout.write(f"  UNEXPECTED: {line}")
        if unexpected:
            raise CommandError("Existing workouts, sets or plans changed during the deploy.")
        self.stdout.write(
            f"Only expected changes ({len(expected)} old time sets now in seconds)."
            if expected
            else "No changes to existing training data."
        )
