"""Feedback reports: the dialog, saving, the hourly limit, the email, admin and commands."""

import pytest
from allauth.account.models import EmailAddress
from django.core.mail.backends.base import BaseEmailBackend
from django.core.management import call_command
from django.urls import reverse
from django.utils import translation

from feedback.models import Device, Feedback, Kind, Status
from feedback.services import HOURLY_LIMIT, device_from_user_agent, page_path

HTMX = {"HTTP_HX_REQUEST": "true"}
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)
URL = "/feedback/"


@pytest.fixture(autouse=True)
def _polish(settings):
    """These tests check the Polish texts the feedback feature had before PL/EN: they are
    translations of English msgids now, so the whole module runs in Polish."""
    settings.LANGUAGE_CODE = "pl"
    with translation.override("pl"):
        yield


@pytest.fixture
def logged_in(client, user):
    user.email = "ania@example.com"
    user.save()
    client.force_login(user)
    return client


@pytest.fixture
def owner_inbox(settings):
    settings.FEEDBACK_EMAIL = "owner@example.com"


def _send(client, message="Timer nie dzwoni po przerwie.", kind="bug", **extra):
    data = {"feedback-kind": kind, "feedback-message": message, "feedback-page": "/plans/"}
    return client.post(URL, data, **extra)


# --- device and page ----------------------------------------------------------------


@pytest.mark.parametrize(
    "user_agent, device",
    [
        (IPHONE, Device.PHONE),
        ("Mozilla/5.0 (Linux; Android 14; Pixel 8) ... Mobile Safari/537.36", Device.PHONE),
        ("Mozilla/5.0 (Linux; Android 14; SM-X710) ... Safari/537.36", Device.TABLET),
        ("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) ...", Device.TABLET),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/130 Safari/537.36", Device.COMPUTER),
        ("", Device.UNKNOWN),
    ],
)
def test_device_from_user_agent(user_agent, device):
    assert device_from_user_agent(user_agent) == device


@pytest.mark.parametrize(
    "url, path",
    [
        ("https://liftlog-sebt.onrender.com/workouts/12/?add=3", "/workouts/12/?add=3"),
        ("/plans/", "/plans/"),
        ("//evil.example/x", "/x"),  # the other host is dropped, only our path stays
        ("javascript:alert(1)", ""),
        ("", ""),
    ],
)
def test_page_path_keeps_only_our_path(url, path):
    assert page_path(url) == path


# --- the dialog ---------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name", ["home", "plans:plan_list", "exercises:exercise_list", "settings"]
)
def test_every_screen_has_the_report_link_and_dialog(logged_in, url_name):
    content = logged_in.get(reverse(url_name)).content.decode()

    assert "data-feedback-open" in content and ">Zgłoś</a>" in content
    assert '<dialog class="feedback-dialog"' in content
    for label in ("Błąd", "Sugestia zmiany", "Opinia", "Wyślij"):
        assert label in content
    assert "Opisz, co się wydarzyło albo co proponujesz" in content


@pytest.mark.django_db
def test_workout_screen_has_it_without_clashing_with_the_set_form(
    logged_in, user, make_workout, bench
):
    workout = make_workout(user, days_ago=0, finished=False)

    content = logged_in.get(
        reverse("workouts:workout_detail", args=[workout.pk]), {"add": bench.pk}
    ).content.decode()

    assert '<dialog class="feedback-dialog"' in content
    assert 'name="feedback-message"' in content  # prefixed: no clash with set fields
    assert 'hx-post="/feedback/" hx-target="this" hx-swap="outerHTML"' in content


@pytest.mark.django_db
def test_logged_out_pages_have_no_report_link(client):
    content = client.get(reverse("account_login")).content.decode()

    assert "data-feedback-open" not in content and "feedback-dialog" not in content


# --- sending --------------------------------------------------------------------------


@pytest.mark.django_db
def test_htmx_send_saves_everything_and_answers_with_thanks_only(logged_in, user):
    response = _send(
        logged_in,
        HTTP_HX_CURRENT_URL="https://liftlog-sebt.onrender.com/workouts/7/?add=3",
        HTTP_USER_AGENT=IPHONE,
        **HTMX,
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Dzięki! Zgłoszenie dotarło." in content
    assert "<html" not in content  # just the piece that replaces the form
    report = Feedback.objects.get()
    assert (report.user, report.kind, report.status) == (user, Kind.BUG, Status.NEW)
    assert report.message == "Timer nie dzwoni po przerwie."
    assert report.page == "/workouts/7/?add=3"  # the page it was sent from
    assert report.device == Device.PHONE
    assert report.user_agent == IPHONE
    assert report.created_at is not None


@pytest.mark.django_db
def test_without_javascript_it_goes_back_with_the_message(logged_in):
    response = _send(logged_in, follow=True)

    assert response.redirect_chain[-1][0] == "/plans/"
    assert "Dzięki! Zgłoszenie dotarło." in response.content.decode()
    assert Feedback.objects.get().page == "/plans/"


@pytest.mark.django_db
def test_never_redirects_to_another_site(logged_in):
    data = {"feedback-kind": "bug", "feedback-message": "x", "feedback-page": "//evil.example/"}

    response = logged_in.post(URL, data)

    assert response.url == reverse("home")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind, message, error",
    [
        ("bug", "", "Napisz kilka słów"),
        ("bug", "   ", "Napisz kilka słów"),
        ("bug", "x" * 2001, "Maksymalnie 2000 znaków"),
        ("spam", "Hej", "Wybierz rodzaj zgłoszenia."),
    ],
)
def test_invalid_reports_show_the_form_again_with_errors(logged_in, kind, message, error):
    response = _send(logged_in, message=message, kind=kind, **HTMX)

    content = response.content.decode()
    assert error in content
    assert 'class="form feedback-form"' in content
    assert not Feedback.objects.exists()


@pytest.mark.django_db
def test_hourly_limit_per_user(logged_in, other_user, client):
    for _ in range(HOURLY_LIMIT):
        _send(logged_in, **HTMX)

    blocked = _send(logged_in, **HTMX)

    assert f"Wysłano już {HOURLY_LIMIT} zgłoszeń" in blocked.content.decode()
    assert Feedback.objects.count() == HOURLY_LIMIT
    # Another user isn't affected.
    client.force_login(other_user)
    assert "Dzięki!" in _send(client, **HTMX).content.decode()


@pytest.mark.django_db
def test_old_reports_dont_count_towards_the_limit(logged_in, user):
    from datetime import timedelta

    from django.utils import timezone

    for _ in range(HOURLY_LIMIT):
        _send(logged_in, **HTMX)
    Feedback.objects.update(created_at=timezone.now() - timedelta(minutes=61))

    assert "Dzięki!" in _send(logged_in, **HTMX).content.decode()


@pytest.mark.django_db
def test_login_required(client):
    response = client.post(URL, {"feedback-kind": "bug", "feedback-message": "x"})

    assert response.status_code == 302
    assert not Feedback.objects.exists()


@pytest.mark.django_db
def test_feedback_page_works_without_javascript(logged_in):
    content = logged_in.get(URL, {"page": "/plans/"}).content.decode()

    assert "<h1>Zgłoś</h1>" in content
    assert 'name="feedback-page" value="/plans/"' in content


# --- the email ----------------------------------------------------------------------------


@pytest.mark.django_db
def test_each_report_is_emailed_to_the_owner(logged_in, owner_inbox, mailoutbox):
    _send(
        logged_in,
        kind="suggestion",
        message="Dodajcie ciemniejszy motyw.",
        HTTP_USER_AGENT=IPHONE,
        **HTMX,
    )

    report = Feedback.objects.get()
    (mail,) = mailoutbox
    assert mail.to == ["owner@example.com"]
    assert mail.reply_to == ["ania@example.com"]
    assert mail.subject == f"[LiftLog] Sugestia zmiany #{report.pk}: Dodajcie ciemniejszy motyw."
    for text in ("Rodzaj: Sugestia zmiany", "Użytkownik: ania <ania@example.com>",
                 "Strona: /plans/", "Urządzenie: Telefon", "Dodajcie ciemniejszy motyw.",
                 f"http://testserver/admin/feedback/feedback/{report.pk}/change/"):  # fmt: skip
        assert text in mail.body, text


class FailingBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise ConnectionError("Brevo is down")


@pytest.mark.django_db
def test_a_failed_email_keeps_the_report_and_logs_the_error(
    logged_in, owner_inbox, settings, caplog
):
    settings.EMAIL_BACKEND = "feedback.tests.test_feedback.FailingBackend"

    response = _send(logged_in, **HTMX)

    assert "Dzięki! Zgłoszenie dotarło." in response.content.decode()
    report = Feedback.objects.get()
    assert f"Feedback #{report.pk} saved, but the email to the owner failed" in caplog.text
    assert "ania@example.com" not in caplog.text


@pytest.mark.django_db
def test_without_feedback_email_reports_are_only_saved(logged_in, settings, mailoutbox, caplog):
    settings.FEEDBACK_EMAIL = ""

    _send(logged_in, **HTMX)

    assert Feedback.objects.count() == 1
    assert mailoutbox == []
    assert "FEEDBACK_EMAIL is not set" in caplog.text


# --- admin --------------------------------------------------------------------------------


@pytest.fixture
def admin_client(client, django_user_model):
    admin = django_user_model.objects.create_superuser("szef", "szef@example.com", "x")
    client.force_login(admin)
    return client


@pytest.fixture
def reports(user):
    return [
        Feedback.objects.create(user=user, kind=Kind.BUG, message="Crash na treningu"),
        Feedback.objects.create(
            user=user, kind=Kind.OPINION, message="Super apka", status=Status.DONE
        ),
    ]


@pytest.mark.django_db
def test_admin_lists_and_filters_reports(admin_client, reports):
    url = reverse("admin:feedback_feedback_changelist")

    everything = admin_client.get(url).content.decode()
    bugs = admin_client.get(url, {"kind__exact": "bug"}).content.decode()
    done = admin_client.get(url, {"status__exact": "done"}).content.decode()

    assert "Crash na treningu" in everything and "Super apka" in everything
    assert "Crash na treningu" in bugs and "Super apka" not in bugs
    assert "Super apka" in done and "Crash na treningu" not in done


@pytest.mark.django_db
def test_admin_changes_status_from_the_list(admin_client, reports):
    bug = reports[0]
    url = reverse("admin:feedback_feedback_changelist")

    admin_client.post(url, {"action": "mark_in_progress", "_selected_action": [bug.pk]})

    bug.refresh_from_db()
    assert bug.status == Status.IN_PROGRESS


@pytest.mark.django_db
def test_admin_login_goes_through_the_app_login(client, logged_in, user):
    client.logout()
    assert client.get("/admin/").url.startswith("/admin/login/")
    assert client.get("/admin/login/").url.startswith(reverse("account_login"))
    # A normal user who is logged in still can't get in.
    client.force_login(user)
    assert client.get("/admin/login/").status_code == 403


# --- commands -------------------------------------------------------------------------------


@pytest.mark.django_db
def test_feedback_report_groups_open_reports_by_kind(reports, user, capsys):
    Feedback.objects.create(
        user=user, kind=Kind.SUGGESTION, message="Ciemny motyw\nproszę", page="/plans/"
    )

    call_command("feedback_report")

    out = capsys.readouterr().out
    assert out.index("== Błąd (1)") < out.index("== Sugestia zmiany (1)")
    assert "Crash na treningu" in out
    assert "    Ciemny motyw\n    proszę" in out
    assert "Super apka" not in out  # done
    assert "Open reports: 2." in out


@pytest.mark.django_db
def test_feedback_report_all_includes_done(reports, capsys):
    call_command("feedback_report", all=True)

    assert "Super apka" in capsys.readouterr().out


@pytest.mark.django_db
def test_feedback_report_when_nothing_is_open(capsys):
    call_command("feedback_report")

    assert "No open reports." in capsys.readouterr().out


@pytest.mark.django_db
def test_grant_admin_needs_a_confirmed_address(user, other_user, capsys, monkeypatch):
    user.email = "owner@example.com"
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    other_user.email = "fake@example.com"
    other_user.save()
    EmailAddress.objects.create(
        user=other_user, email=other_user.email, verified=False, primary=True
    )
    monkeypatch.setenv("ADMIN_EMAILS", "OWNER@example.com, fake@example.com")

    call_command("grant_admin")

    user.refresh_from_db()
    other_user.refresh_from_db()
    assert user.is_staff and user.is_superuser
    assert not other_user.is_staff
    out = capsys.readouterr().out
    assert "ania is now an admin" in out
    assert "@" not in out  # no addresses in the deploy log

    call_command("grant_admin", "owner@example.com")
    assert "already has admin access" in capsys.readouterr().out


@pytest.mark.django_db
def test_grant_admin_without_emails_does_nothing(capsys, monkeypatch):
    monkeypatch.delenv("ADMIN_EMAILS", raising=False)

    call_command("grant_admin")

    assert "no emails given" in capsys.readouterr().out
