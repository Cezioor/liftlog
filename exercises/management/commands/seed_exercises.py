from django.core.management.base import BaseCommand
from django.db import transaction

from exercises.models import Exercise
from exercises.seed_data import (
    ALIASES,
    EXERCISE_TYPES,
    EXERCISES,
    EXTRA_EXERCISES,
    PROGRESSION_STEP_OVERRIDES,
)
from exercises.services import default_progression_step


class Command(BaseCommand):
    help = "Create or update the built-in exercise library. Safe to run many times."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for name, muscle_group, equipment, is_bodyweight in EXERCISES:
            step = PROGRESSION_STEP_OVERRIDES.get(
                name, default_progression_step(muscle_group, equipment)
            )
            measurement, category, unilateral = EXERCISE_TYPES.get(
                name, ("weight_reps", "strength", False)
            )
            # update_or_create makes the command idempotent: running it again
            # updates existing built-ins instead of creating duplicates.
            _, created = Exercise.objects.update_or_create(
                name=name,
                owner=None,
                defaults={
                    "muscle_group": muscle_group,
                    "equipment": equipment,
                    "is_bodyweight": is_bodyweight,
                    "progression_step_kg": step,
                    "aliases": ALIASES.get(name, ""),
                    "measurement": measurement,
                    "category": category,
                    "is_unilateral": unilateral,
                },
            )
            created_count += created

        for extra in EXTRA_EXERCISES:
            defaults = {key: value for key, value in extra.items() if key != "name"}
            defaults["is_bodyweight"] = extra["equipment"] == "bodyweight"
            defaults["progression_step_kg"] = default_progression_step(
                extra["muscle_group"], extra["equipment"]
            )
            _, created = Exercise.objects.update_or_create(
                name=extra["name"], owner=None, defaults=defaults
            )
            created_count += created

        updated_count = len(EXERCISES) + len(EXTRA_EXERCISES) - created_count
        self.stdout.write(
            self.style.SUCCESS(
                f"Built-in exercises: {created_count} created, {updated_count} updated."
            )
        )
