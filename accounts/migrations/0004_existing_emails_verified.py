"""Accounts that existed before email verification count as verified.

With ACCOUNT_EMAIL_VERIFICATION = "mandatory", allauth only lets a user in once their
address is confirmed. Accounts created earlier never got a link, so without this they
would be locked out. For every user with an email, an allauth EmailAddress row is
created as verified and primary. User rows themselves are not changed.

Special cases are listed in the deploy log (by username, not by address):
- users without an email can't log in by email: set one in the admin;
- two users with the same address (any letter case): only the oldest is verified,
  because a verified address must be unique.
"""

from django.db import migrations


def mark_existing_emails_verified(apps, schema_editor=None, report=print):
    User = apps.get_model("accounts", "User")
    EmailAddress = apps.get_model("account", "EmailAddress")

    taken = {e.lower() for e in EmailAddress.objects.filter(verified=True).values_list("email", flat=True)}
    verified = []
    for user in User.objects.order_by("pk"):
        email = (user.email or "").strip().lower()
        if not email:
            report(f"  no email, can't log in by email: user {user.pk} ({user.username})")
            continue
        if EmailAddress.objects.filter(user=user).exists():
            continue  # already handled (e.g. signed up through allauth)
        duplicate = email in taken
        EmailAddress.objects.create(
            user=user, email=email, verified=not duplicate, primary=True
        )
        if duplicate:
            report(f"  same email as an older account, left unverified: user {user.pk} ({user.username})")
        else:
            taken.add(email)
            verified.append(user.pk)
    report(f"  existing accounts marked as verified: {len(verified)}")
    return verified


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_effort_scale"),
        ("account", "0009_emailaddress_unique_primary_email"),
    ]

    operations = [
        # Reversing removes nothing: the addresses stay (harmless without allauth).
        migrations.RunPython(mark_existing_emails_verified, migrations.RunPython.noop),
    ]
