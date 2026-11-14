from django.core.management.base import BaseCommand

from exercises.instructions_pl import apply_translations, load_translations


class Command(BaseCommand):
    help = "Load the Polish instructions of built-in exercises. Safe to run many times."

    def handle(self, *args, **options):
        translations = load_translations()
        updated, stale = apply_translations(translations)
        for name in stale:
            self.stdout.write(
                self.style.WARNING(f"English steps changed since the translation: {name}")
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Polish instructions: {len(translations)} in the file, {updated} rows updated."
            )
        )
