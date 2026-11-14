from django.core.management.base import BaseCommand
from django.db import transaction

from exercises.models import Equipment, Exercise
from exercises.services import default_progression_step
from exercises.smith_variants import (
    BASELESS_LEVELS,
    FREE_WEIGHT_PHOTO_NOTE,
    FREE_WEIGHTS,
    NO_BASE_PHOTOS,
    SMITH_VARIANTS,
)


class Command(BaseCommand):
    help = "Create or update the built-in Smith machine variants. Safe to run many times."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count, missing_bases = 0, []
        for (
            name, base_name, aliases, muscle_group, primary, secondary,
            measurement, unilateral, instructions,
        ) in SMITH_VARIANTS:  # fmt: skip
            base = None
            if base_name:
                base = Exercise.objects.filter(name=base_name, owner=None).first()
                if base is None:
                    missing_bases.append(base_name)
            images = list(base.images) if base and name not in NO_BASE_PHOTOS else []
            note = FREE_WEIGHT_PHOTO_NOTE if images and base.equipment in FREE_WEIGHTS else ("", "")
            _, created = Exercise.objects.update_or_create(
                name=name,
                owner=None,
                defaults={
                    "aliases": aliases,
                    "muscle_group": muscle_group,
                    "equipment": Equipment.SMITH,
                    "is_bodyweight": False,
                    "measurement": measurement,
                    "category": "strength",
                    "is_unilateral": unilateral,
                    "primary_muscles": primary,
                    "secondary_muscles": secondary,
                    "instructions": instructions,
                    # The base's photos (free weights, same movement), as for user variants.
                    "images": images,
                    "photo_note": note[0],
                    "photo_note_pl": note[1],
                    "level": base.level if base else BASELESS_LEVELS.get(name, ""),
                    "mechanic": base.mechanic if base else "",
                    "progression_step_kg": default_progression_step(muscle_group, Equipment.SMITH),
                },
            )
            created_count += created
        updated = len(SMITH_VARIANTS) - created_count
        self.stdout.write(
            self.style.SUCCESS(
                f"Smith machine variants: {created_count} created, {updated} updated."
            )
        )
        if missing_bases:
            # A fresh database before the import: the next run links them.
            self.stdout.write(f"Base exercises not found (yet): {', '.join(missing_bases)}")
