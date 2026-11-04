from django.core.management.base import BaseCommand
from django.db import transaction

from exercises.models import Exercise
from exercises.seed_data import EXERCISES


class Command(BaseCommand):
    help = "Create or update the built-in exercise library. Safe to run many times."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for name, muscle_group, equipment, is_bodyweight in EXERCISES:
            # update_or_create makes the command idempotent: running it again
            # updates existing built-ins instead of creating duplicates.
            _, created = Exercise.objects.update_or_create(
                name=name,
                owner=None,
                defaults={
                    "muscle_group": muscle_group,
                    "equipment": equipment,
                    "is_bodyweight": is_bodyweight,
                },
            )
            created_count += created
        updated_count = len(EXERCISES) - created_count
        self.stdout.write(
            self.style.SUCCESS(
                f"Built-in exercises: {created_count} created, {updated_count} updated."
            )
        )
