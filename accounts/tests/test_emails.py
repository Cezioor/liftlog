"""Optional email verification, the account emails (Polish, HTML + text), mail failures."""

import importlib
import json
import re
from html.parser import HTMLParser
from unittest import mock

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.urls import reverse
from django.utils import translation

from accounts.adapter import SIGNUP_DONE, SIGNUP_MAIL_FAILED

User = get_user_model()
PASSWORD = "Squat-Heavy-2026"


def _signup(client, email="ania@example.com"):
    return client.post(
        reverse("account_signup"),
        {"email": email, "password1": PASSWORD, "password2": PASSWORD},
        follow=True,
    )


@pytest.fixture
def optional(settings):
    settings.ACCOUNT_EMAIL_VERIFICATION = "optional"


@pytest.fixture
def polish(settings):
    """The sign-up messages were Polish before PL/EN; now they are translations of English
    msgids, so these tests check them in Polish (str() of the lazy text, in Polish)."""
    settings.LANGUAGE_CODE = "pl"
    with translation.override("pl"):
        yield


# --- the switch -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "env, expected", [(None, "mandatory"), ("optional", "optional"), (" mandatory ", "mandatory")]
)
def test_verification_mode_comes_from_the_environment(monkeypatch, env, expected):
    import config.settings

    # Only the environment given here: a developer's .env (e.g. optional) must not leak in.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    if env is None:
        monkeypatch.delenv("ACCOUNT_EMAIL_VERIFICATION", raising=False)
    else:
        monkeypatch.setenv("ACCOUNT_EMAIL_VERIFICATION", env)
    try:
        assert importlib.reload(config.settings).ACCOUNT_EMAIL_VERIFICATION == expected
    finally:
        monkeypatch.delenv("ACCOUNT_EMAIL_VERIFICATION", raising=False)
        importlib.reload(config.settings)


def test_a_typo_in_the_mode_stops_the_app_instead_of_guessing(monkeypatch):
    import config.settings

    monkeypatch.setenv("ACCOUNT_EMAIL_VERIFICATION", "optinal")
    try:
        with pytest.raises(ImproperlyConfigured):
            importlib.reload(config.settings)
    finally:
        monkeypatch.delenv("ACCOUNT_EMAIL_VERIFICATION")
        importlib.reload(config.settings)


# --- optional verification ----------------------------------------------------------------


@pytest.mark.django_db
def test_optional_signup_logs_in_and_says_a_link_was_sent(client, optional, polish, mailoutbox):
    response = _signup(client)

    assert response.redirect_chain[-1][0] == reverse("home")
    assert "_auth_user_id" in client.session
    assert str(SIGNUP_DONE) in response.content.decode()
    assert "Konto założone. Wysłaliśmy też link" in response.content.decode()
    assert len(mailoutbox) == 1
    assert not EmailAddress.objects.get().verified


@pytest.mark.django_db
def test_settings_page_offers_the_link_again_until_confirmed(client, optional, mailoutbox):
    from django.core.cache import cache

    _signup(client)
    page = client.get(reverse("settings")).content.decode()
    assert "not confirmed yet" in page
    assert "Send the confirmation link again" in page

    cache.clear()  # past the 3-minute limit
    client.post(reverse("account_email"), {"email": "ania@example.com", "action_send": ""})
    assert len(mailoutbox) == 2

    EmailAddress.objects.update(verified=True)
    assert "not confirmed yet" not in client.get(reverse("settings")).content.decode()


@pytest.mark.django_db
def test_mandatory_signup_shows_the_check_your_email_page_not_the_message(client, mailoutbox):
    response = _signup(client)

    content = response.content.decode()
    assert "Account created!" in content
    assert str(SIGNUP_DONE) not in content
    assert "_auth_user_id" not in client.session


# --- when the mail service fails ---------------------------------------------------------


class FailingBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise ConnectionError("mail service down")


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["optional", "mandatory"])
def test_signup_survives_a_mail_failure_and_says_so(client, settings, caplog, polish, mode):
    settings.ACCOUNT_EMAIL_VERIFICATION = mode
    settings.EMAIL_BACKEND = "accounts.tests.test_emails.FailingBackend"

    response = _signup(client)

    assert response.status_code == 200
    assert User.objects.filter(email="ania@example.com").exists()
    content = response.content.decode()
    assert str(SIGNUP_MAIL_FAILED) in content
    assert "nie udało się wysłać linku" in content
    assert str(SIGNUP_DONE) not in content
    assert "Sending email account/email/email_confirmation_signup failed" in caplog.text
    assert "ania@example.com" not in caplog.text  # no personal data in logs


# --- the email itself ----------------------------------------------------------------------


class _Html(HTMLParser):
    """Collects visible text, links, tags and inline styles of an HTML email."""

    def __init__(self):
        super().__init__()
        self.text, self.hrefs, self.tags, self.styles = [], [], set(), []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.add(tag)
        if tag in ("title", "style", "head"):
            self._skip += 1
        if "href" in attrs:
            self.hrefs.append(attrs["href"])
        if "style" in attrs:
            self.styles.append(attrs["style"])

    def handle_endtag(self, tag):
        if tag in ("title", "style", "head"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.text.append(data.strip())


SPAM_PHRASES = [
    "kliknij tutaj", "click here", "darmow", "za darmo", "free", "pilne", "urgent",
    "gwarant", "wygra", "promocj", "100%", "$", "€", "!!", "act now", "limited time",
]  # fmt: skip


def _check_not_spammy(message, link):
    """Content checks of the kind spam filters score (SpamAssassin-style rules)."""
    subject = message.subject
    assert 10 <= len(subject) <= 60
    assert "!" not in subject
    assert not any(w.isupper() and len(w) > 3 for w in subject.split()), "shouting"

    # Plain text and HTML versions, both carrying the same link.
    assert message.body and link in message.body
    (html, mimetype), *_ = message.alternatives
    assert mimetype == "text/html"
    page = _Html()
    page.feed(html)
    visible = " ".join(page.text)

    lowered = (subject + " " + message.body + " " + visible).lower()
    for phrase in SPAM_PHRASES:
        assert phrase not in lowered, phrase

    assert html.lstrip().startswith("<!doctype html>") and '<html lang="pl">' in html
    assert page.tags.isdisjoint({"script", "img", "form", "iframe", "link", "style"})
    assert all("display:none" not in s.replace(" ", "") for s in page.styles), "hidden text"
    # Every link goes to the app itself (no shorteners, no other domains), and the
    # main link is also printed as text, so the button's target is visible.
    assert page.hrefs and all(h.startswith("http://testserver/") for h in page.hrefs)
    assert link in visible
    # Mostly real text, not markup: well over 100 visible characters.
    assert len(visible) > 200


@pytest.mark.django_db
def test_signup_email_is_polish_html_plus_text_and_not_spammy(client, mailoutbox):
    _signup(client)

    message = mailoutbox[0]
    link = re.search(r"http://testserver/accounts/confirm-email/\S+", message.body).group(0)
    assert message.subject == "Potwierdź adres e-mail w LiftLog"
    assert "dziękujemy za założenie konta w LiftLog" in message.body
    assert "Jeśli to nie Ty" in message.body
    _check_not_spammy(message, link)


@pytest.mark.django_db
def test_password_reset_email_is_polish_html_plus_text_and_not_spammy(client, mailoutbox):
    user = User.objects.create_user(username="ania", email="ania@example.com", password=PASSWORD)
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

    client.post(reverse("account_reset_password"), {"email": "ania@example.com"})

    message = mailoutbox[0]
    link = re.search(r"http://testserver/accounts/password/reset/key/\S+", message.body).group(0)
    assert message.subject == "Ustaw nowe hasło w LiftLog"
    _check_not_spammy(message, link)


@pytest.mark.django_db
def test_brevo_receives_polish_subject_html_and_text(client, settings):
    """What actually goes to Brevo's API (HTTP mocked): anymail must not reject the
    Polish characters, and both bodies must be there."""
    settings.EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    settings.ANYMAIL = {"BREVO_API_KEY": "test-key-not-real"}
    settings.DEFAULT_FROM_EMAIL = "LiftLog <liftlog@example.com>"
    response = mock.Mock(status_code=201, text='{"messageId": "<1@brevo>"}')
    response.json.return_value = {"messageId": "<1@brevo>"}

    with mock.patch("requests.Session.request", return_value=response) as request:
        _signup(client)

    payload = json.loads(request.call_args.kwargs["data"])
    assert request.call_args.kwargs["url"] == "https://api.brevo.com/v3/smtp/email"
    assert payload["subject"] == "Potwierdź adres e-mail w LiftLog"
    assert payload["sender"] == {"email": "liftlog@example.com", "name": "LiftLog"}
    assert "Potwierdź adres e-mail" in payload["htmlContent"]
    assert "dziękujemy za założenie konta" in payload["textContent"]
