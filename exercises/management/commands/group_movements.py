from django.core.management.base import BaseCommand

from exercises.movements import group_movements, pending_groups


class Command(BaseCommand):
    help = "Group built-in exercises that differ only by equipment into movement families."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pending", action="store_true", help="Only list doubtful groups to decide on."
        )

    def handle(self, *args, pending=False, **options):
        if pending:
            for group in pending_groups():
                self.stdout.write(f"{group.describe()}  ({'; '.join(group.doubts)})")
            return
        report = group_movements()
        self.stdout.write(
            self.style.SUCCESS(
                f"Movement families: {report.families} ({report.exercises} exercises, "
                f"{report.created} new)."
            )
        )
        if report.pending:
            self.stdout.write(
                f"Waiting for confirmation: {len(report.pending)} doubtful groups "
                "(see exercises/movement_groups.py)."
            )
