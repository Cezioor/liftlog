"""Print a fingerprint of the user's training data: workouts, sets and plans.

build.sh runs it before the migrations and again after the exercise import and fails the
deploy if the two differ, which proves a deploy left existing data untouched.

Only columns that existed before Stage 1.6 are read, so the command also works on a
database whose migrations haven't run yet.
"""

import hashlib

from django.core.management.base import BaseCommand
from django.db import DatabaseError

from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import Workout, WorkoutSet

FIELDS = {
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
    # Decimal('60.00') and Decimal('60') must hash the same.
    if hasattr(value, "normalize"):
        return format(value.normalize(), "f")
    return value


def fingerprint():
    digest = hashlib.sha256()
    counts = []
    for model, fields in FIELDS.items():
        rows = model.objects.order_by("pk").values_list(*fields)
        count = 0
        for row in rows.iterator(chunk_size=2000):
            digest.update(repr(tuple(_normalise(v) for v in row)).encode())
            count += 1
        counts.append(f"{model.__name__}={count}")
    return " ".join(counts) + " sha256=" + digest.hexdigest()[:16]


class Command(BaseCommand):
    help = "Print a fingerprint of workouts, sets and plans (to prove a deploy changed nothing)."

    def handle(self, *args, **options):
        try:
            self.stdout.write(fingerprint())
        except DatabaseError:
            # Brand-new database: the tables don't exist yet.
            self.stdout.write("empty")
