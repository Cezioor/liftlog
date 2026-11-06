"""Sign-up with email verification, log-in by email, password reset (django-allauth)."""

import importlib
import re

import pytest
from allauth.account.models import EmailAddress
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse

from workouts.management.commands.data_fingerprint import compare, snapshot

User = get_user_model()
PASSWORD = "Squat-Heavy-2026"


def _signup(client, email="ania@example.com", password=PASSWORD, password2=None):
    return client.post(
        reverse("account_signup"),
        {"email": email, "password1": password, "password2": password2 or password},
    )


def _link(mail):
    return re.search(r"https?://\S+", mail.body).group(0)


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user(username="ania", email="ania@example.com", password=PASSWORD)
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


# --- sign-up ------------------------------------------------------------------------


@pytest.mark.django_db
def test_signup_sends_a_link_and_shows_check_your_email(client, mailoutbox):
    response = _signup(client)

    assert response.status_code == 302
    assert response.url == reverse("account_email_verification_sent")
    user = User.objects.get(email="ania@example.com")
    assert not EmailAddress.objects.get(user=user).verified
    assert "_auth_user_id" not in client.session  # no access before confirming
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["ania@example.com"]
    assert mailoutbox[0].subject == "Potwierdź adres e-mail w LiftLog"
    assert "/accounts/confirm-email/" in _link(mailoutbox[0])

    page = client.get(response.url).content.decode()
    assert "Account created!" in page
    assert "We sent a link to <strong>ania@example.com</strong>" in page
    assert "Click it to activate your account." in page
    assert "Check your spam folder or send it again." in page
    assert "Send the link again" in page


@pytest.mark.django_db
def test_clicking_the_link_activates_the_account_and_logs_in(client, mailoutbox):
    _signup(client)
    link = _link(mailoutbox[0])

    page = client.get(link)
    assert "Activate my account" in page.content.decode()
    assert not EmailAddress.objects.get().verified  # opening the link alone does nothing

    response = client.post(link)
    assert response.status_code == 302
    assert response.url == reverse("home")
    assert EmailAddress.objects.get().verified
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_cannot_log_in_before_confirming(client, mailoutbox):
    _signup(client)

    response = client.post(
        reverse("account_login"), {"login": "ania@example.com", "password": PASSWORD}
    )

    assert response.status_code == 302
    assert response.url == reverse("account_email_verification_sent")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_resend_link_is_rate_limited(client, mailoutbox):
    _signup(client)
    resend = reverse("resend_verification")

    response = client.post(resend, follow=True)
    assert len(mailoutbox) == 1  # the sign-up email was sent seconds ago
    assert "Wait 3 minutes" in response.content.decode()

    cache.clear()  # as if the 3 minutes had passed
    response = client.post(resend, follow=True)
    assert "Sent! Check your inbox" in response.content.decode()
    assert "Confirmation email sent to" not in response.content.decode()
    assert len(mailoutbox) == 2
    assert mailoutbox[1].to == ["ania@example.com"]


@pytest.mark.django_db
def test_resend_never_mails_an_address_typed_into_the_form(client, mailoutbox):
    response = client.post(reverse("resend_verification"), {"email": "victim@example.com"})

    assert response.url == reverse("account_login")
    assert mailoutbox == []


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["ania@example.com", "Ania@Example.com"])
def test_signup_with_an_existing_email_says_so_with_links(client, verified_user, email):
    response = _signup(client, email=email)

    content = response.content.decode()
    assert response.status_code == 200
    assert "An account with this email already exists." in content
    assert f'<a href="{reverse("account_login")}">Log in</a>' in content
    assert f'<a href="{reverse("account_reset_password")}">reset your password</a>' in content
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_field_errors_are_shown_next_to_their_fields(client):
    response = _signup(client, email="not-an-email", password2="Something-Else-1")

    content = response.content.decode()
    form = response.context["form"]
    assert form.errors["email"] and form.errors["password2"]
    # Each error list sits inside its field's block, right above the input.
    assert re.search(
        r'<ul class="errorlist" id="id_email_errors">.*?</ul>\s*<input[^>]*name="email"',
        content,
        re.S,
    )
    assert re.search(r'<ul class="errorlist" id="id_password2_errors">', content)
    assert not User.objects.exists()


@pytest.mark.django_db
def test_sending_the_form_twice_does_not_crash(client, mailoutbox):
    """The original bug: a second tap sent the form again. Now it's a clear message
    (and forms.js disables the button after the first tap)."""
    _signup(client)
    second = _signup(client)

    assert second.status_code == 200
    assert "An account with this email already exists." in second.content.decode()
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_signup_form_is_submitted_only_once(client):
    content = client.get(reverse("account_signup")).content.decode()

    assert "data-submit-once" in content
    assert 'data-busy-text="Creating your account…"' in content
    assert "js/forms.js" in content


# --- log-in -------------------------------------------------------------------------


@pytest.mark.django_db
def test_login_with_email_and_logout(client, verified_user):
    response = client.post(
        reverse("account_login"), {"login": "ANIA@example.com", "password": PASSWORD}
    )
    assert response.status_code == 302
    assert response.url == reverse("home")
    assert int(client.session["_auth_user_id"]) == verified_user.pk

    response = client.post(reverse("account_logout"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_wrong_password_shows_an_error(client, verified_user):
    response = client.post(
        reverse("account_login"), {"login": "ania@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 200
    assert "not correct" in response.content.decode()


@pytest.mark.django_db
def test_failed_logins_are_limited(client, verified_user):
    data = {"login": "ania@example.com", "password": "wrong-password"}
    pages = [client.post(reverse("account_login"), data).content.decode() for _ in range(6)]

    assert not any("Too many failed login attempts" in page for page in pages[:5])
    assert "Too many failed login attempts" in pages[5]
    # Even the right password is refused until the limit expires (5 minutes).
    right = client.post(reverse("account_login"), {**data, "password": PASSWORD})
    assert right.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_home_requires_login(client):
    response = client.get(reverse("home"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("account_login"))


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["account_login", "account_signup", "account_reset_password"])
def test_auth_pages_render_in_the_app_layout(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200
    assert 'class="topbar"' in response.content.decode()


# --- password reset -----------------------------------------------------------------


@pytest.mark.django_db
def test_password_reset_by_email(client, verified_user, mailoutbox):
    response = client.post(reverse("account_reset_password"), {"email": "ania@example.com"})
    assert response.status_code == 302
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Ustaw nowe hasło w LiftLog"

    # allauth moves the key from the link into the session, then shows the form.
    page = client.get(_link(mailoutbox[0]), follow=True)
    action = page.redirect_chain[-1][0] if page.redirect_chain else _link(mailoutbox[0])
    response = client.post(action, {"password1": "New-Squat-2027", "password2": "New-Squat-2027"})
    assert response.status_code == 302

    verified_user.refresh_from_db()
    assert verified_user.check_password("New-Squat-2027")


@pytest.mark.django_db
def test_password_reset_for_unknown_email_says_so(client, mailoutbox):
    response = client.post(reverse("account_reset_password"), {"email": "nobody@example.com"})

    assert response.status_code == 200
    assert response.context["form"].errors["email"]
    assert mailoutbox == []


# --- existing accounts (migration accounts/0004) ------------------------------------


migration = importlib.import_module("accounts.migrations.0004_existing_emails_verified")


def _mark_verified():
    lines = []
    verified = migration.mark_existing_emails_verified(apps, report=lines.append)
    return verified, lines


@pytest.mark.django_db
def test_existing_accounts_are_marked_verified_and_can_log_in(client):
    old = User.objects.create_user(username="cezary", email="Cezary@Example.com", password=PASSWORD)

    verified, lines = _mark_verified()

    address = EmailAddress.objects.get(user=old)
    assert (address.email, address.verified, address.primary) == ("cezary@example.com", True, True)
    assert verified == [old.pk]
    assert lines[-1] == "  existing accounts marked as verified: 1"
    response = client.post(
        reverse("account_login"), {"login": "cezary@example.com", "password": PASSWORD}
    )
    assert response.url == reverse("home")


@pytest.mark.django_db
def test_migration_reports_accounts_without_email_and_duplicates():
    User.objects.create_user(username="no-email", password=PASSWORD)
    first = User.objects.create_user(username="a1", email="same@example.com")
    second = User.objects.create_user(username="a2", email="SAME@example.com")

    verified, lines = _mark_verified()

    assert verified == [first.pk]
    assert not EmailAddress.objects.get(user=second).verified
    assert any("no email" in line and "no-email" in line for line in lines)
    assert any("left unverified" in line and "a2" in line for line in lines)
    assert not any("@" in line for line in lines)  # no addresses in the deploy log


@pytest.mark.django_db
def test_migration_changes_no_user_rows_and_is_safe_to_rerun(user, other_user):
    before = snapshot()

    _mark_verified()
    verified_again, _ = _mark_verified()

    assert compare(before, snapshot()) == ([], [])
    assert "User" in before and len(before["User"]) == 2
    assert verified_again == []
