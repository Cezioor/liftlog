"""Give accounts access to the Django admin, by email; no passwords in code.

    python manage.py grant_admin you@example.com
    python manage.py grant_admin                 # emails from ADMIN_EMAILS (comma separated)

build.sh runs it on every deploy with ADMIN_EMAILS from Render, after the data check
(the change to the user row is intended). Only an account whose address is confirmed
gets in, so nobody can claim admin rights by signing up with someone's address.
"""

import os

from allauth.account.models import EmailAddress
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Make the accounts with these (confirmed) emails admins."

    def add_arguments(self, parser):
        parser.add_argument("emails", nargs="*")

    def handle(self, *args, emails=(), **options):
        emails = [e.strip() for e in emails] or [
            e.strip() for e in os.environ.get("ADMIN_EMAILS", "").split(",")
        ]
        emails = [e for e in emails if e]
        if not emails:
            self.stdout.write("grant_admin: no emails given (ADMIN_EMAILS is empty).")
            return
        for email in emails:
            address = (
                EmailAddress.objects.filter(email__iexact=email, verified=True)
                .select_related("user")
                .first()
            )
            if address is None:
                # The address itself isn't printed: deploy logs shouldn't hold personal data.
                self.stdout.write("grant_admin: no account with a confirmed address for one email.")
                continue
            user = address.user
            if user.is_staff and user.is_superuser:
                self.stdout.write(f"grant_admin: {user.get_username()} already has admin access.")
                continue
            user.is_staff = user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])
            self.stdout.write(
                self.style.SUCCESS(f"grant_admin: {user.get_username()} is now an admin.")
            )
