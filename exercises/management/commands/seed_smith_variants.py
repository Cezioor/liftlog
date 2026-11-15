from django.core.management.base import BaseCommand
from django.db import transaction

from exercises.free_db import load_dataset
from exercises.merges import merge_into
from exercises.models import Equipment, Exercise
from exercises.services import default_progression_step
from exercises.smith_variants import (
    ABSORBED_SOURCES,
    BASELESS_LEVELS,
    FREE_WEIGHT_PHOTO_NOTE,
    FREE_WEIGHTS,
    OTHER_BASE_PHOTO_NOTE,
    SMITH_VARIANTS,
)


class Command(BaseCommand):
    help = "Create or update the built-in Smith machine variants. Safe to run many times."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count, missing_bases = 0, []
        absorbed_ids = set(ABSORBED_SOURCES.values())
        absorbed_images = {r["id"]: r["images"] for r in load_dataset() if r["id"] in absorbed_ids}
        for (
            name, base_name, aliases, muscle_group, primary, secondary,
            measurement, unilateral, instructions,
        ) in SMITH_VARIANTS:  # fmt: skip
            base = None
            if base_name:
                base = Exercise.objects.filter(name=base_name, owner=None).first()
                if base is None:
                    missing_bases.append(base_name)
            images, note = list(base.images) if base else [], ("", "")
            if name in ABSORBED_SOURCES:
                # Photos of the same exercise under another name: no note needed.
                images = list(absorbed_images[ABSORBED_SOURCES[name]])
            elif images:
                free = base.equipment in FREE_WEIGHTS
                note = FREE_WEIGHT_PHOTO_NOTE if free else OTHER_BASE_PHOTO_NOTE
            variant, created = Exercise.objects.update_or_create(
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
                    # The base's photos (same movement, other equipment), as for user variants.
                    "images": images,
                    "photo_note": note[0],
                    "photo_note_pl": note[1],
                    "level": base.level if base else BASELESS_LEVELS.get(name, ""),
                    "mechanic": base.mechanic if base else "",
                    "progression_step_kg": default_progression_step(muscle_group, Equipment.SMITH),
                },
            )
            created_count += created
            if name in ABSORBED_SOURCES:
                # A built-in copy from older imports: its sets, plan entries and swaps move here.
                copy = Exercise.objects.filter(owner=None, source_id=ABSORBED_SOURCES[name])
                for r in [merge_into(c, variant) for c in copy]:
                    self.stdout.write(
                        f"Folded “{r.source_name}” ({r.source_id}) into “{r.target_name}” "
                        f"({r.target_id}): {r.sets} sets, {r.plan_entries} plan entries, "
                        f"{r.swaps} swaps."
                    )
        updated = len(SMITH_VARIANTS) - created_count
        self.stdout.write(
            self.style.SUCCESS(
                f"Smith machine variants: {created_count} created, {updated} updated."
            )
        )
        if missing_bases:
            # A fresh database before the import: the next run links them.
            self.stdout.write(f"Base exercises not found (yet): {', '.join(missing_bases)}")
