from django.core.management.base import BaseCommand
from django.utils import timezone

from feedback.models import Feedback, Kind, Status


class Command(BaseCommand):
    help = "Print open feedback reports (new and in progress), grouped by kind."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Include reports marked done.")

    def handle(self, *args, all=False, **options):
        reports = Feedback.objects.select_related("user").order_by("created_at")
        if not all:
            reports = reports.exclude(status=Status.DONE)
        if not reports:
            self.stdout.write("No open reports.")
            return
        for kind in Kind:
            group = [r for r in reports if r.kind == kind]
            if not group:
                continue
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n== {kind.label} ({len(group)})"))
            for r in group:
                who = r.user.email if r.user else "(deleted account)"
                when = timezone.localtime(r.created_at).strftime("%Y-%m-%d %H:%M")
                self.stdout.write(
                    f"\n#{r.pk} · {r.get_status_display()} · {when} · {who} · "
                    f"{r.get_device_display()} · {r.page or '–'}"
                )
                for line in r.message.splitlines() or [""]:
                    self.stdout.write(f"    {line}")
        self.stdout.write(f"\nOpen reports: {len(reports)}.")
