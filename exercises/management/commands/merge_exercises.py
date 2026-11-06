from django.core.management.base import BaseCommand

from exercises.merges import apply_merges


class Command(BaseCommand):
    help = "Merge users' own exercises into the built-in ones listed in exercises/merges.py."

    def handle(self, *args, **options):
        results = apply_merges()
        for r in results:
            self.stdout.write(
                f"  merged exercise {r.source_id} “{r.source_name}” of {r.owner} into "
                f"{r.target_id} “{r.target_name}”: {r.sets} sets, "
                f"{r.plan_entries} plan entries, {r.swaps} swaps moved"
            )
        total = sum(r.sets for r in results)
        self.stdout.write(
            self.style.SUCCESS(f"Merged exercises: {len(results)} ({total} sets moved).")
        )
