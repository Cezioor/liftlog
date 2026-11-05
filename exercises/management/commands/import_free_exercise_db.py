from django.core.management.base import BaseCommand, CommandError

from exercises.free_db import DATA_FILE, PENDING_MATCHES, import_dataset, load_dataset
from workouts.models import Workout, WorkoutSet


class Command(BaseCommand):
    help = (
        "Import free-exercise-db (exercises/data/free_exercise_db.json) as built-in exercises. "
        "Safe to run many times; never deletes or duplicates the original 65 exercises."
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(DATA_FILE), help="Path to exercises.json")

    def handle(self, *args, file, **options):
        # Workouts are never touched; the counts prove it in the deploy log.
        before = (Workout.objects.count(), WorkoutSet.objects.count())
        report = import_dataset(load_dataset(file))
        after = (Workout.objects.count(), WorkoutSet.objects.count())
        if before != after:
            raise CommandError(f"Workout data changed during import: {before} -> {after}")

        self.stdout.write(
            self.style.SUCCESS(
                f"free-exercise-db: {report.created} created, {report.updated} updated, "
                f"{len(report.legacy_matched)} original exercises enriched, "
                f"{report.withheld} withheld until confirmed."
            )
        )
        self.stdout.write(f"Workouts unchanged: {after[0]} workouts, {after[1]} sets.")
        pending = [name for name, candidates in PENDING_MATCHES.items() if candidates]
        if pending:
            self.stdout.write(f"Waiting for confirmation: {', '.join(pending)}.")
        for name in report.legacy_missing:
            self.stdout.write(self.style.WARNING(f"Original exercise not found: {name}"))
        for source_id, reason in report.conflicts:
            self.stdout.write(self.style.WARNING(f"Skipped {source_id}: {reason}"))
