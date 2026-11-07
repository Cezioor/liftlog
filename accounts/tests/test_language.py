"""PL/EN: which language a page is in, the switcher, Settings, sign-up and logging in.

The order is: the language saved on the account, the cookie, the browser's
Accept-Language, English (config.middleware.UserLanguageMiddleware). English is the
default, so each step is tested by making it win with Polish.
"""

import re

import pytest
from allauth.account.models import EmailAddress
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import UserSettings
from accounts.services import account_language

User = get_user_model()
PASSWORD = "Squat-Heavy-2026"
COOKIE = django_settings.LANGUAGE_COOKIE_NAME
SWITCHER = 'class="language-switcher"'


def _language(response):
    return response["Content-Language"]


def _set_account_language(user, language):
    UserSettings.objects.update_or_create(user=user, defaults={"language": language})


def _verified_user(language=""):
    user = User.objects.create_user(username="ania", email="ania@example.com", password=PASSWORD)
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    if language:
        _set_account_language(user, language)
    return user


def _log_in(client, **headers):
    return client.post(
        reverse("account_login"), {"login": "ania@example.com", "password": PASSWORD}, **headers
    )


# --- the order --------------------------------------------------------------------------


def test_the_app_is_english_by_default_and_offers_polish_and_english():
    import config.settings

    assert config.settings.LANGUAGE_CODE == "en"
    assert [code for code, _ in config.settings.LANGUAGES] == ["pl", "en"]


@pytest.mark.django_db
def test_without_cookie_or_browser_language_the_page_is_english(client):
    response = client.get(reverse("account_login"))

    assert _language(response) == "en"
    assert '<html lang="en">' in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "header, expected",
    [
        ("pl-PL,pl;q=0.9,en;q=0.8", "pl"),
        ("en-GB,en;q=0.9", "en"),
        ("de-DE,de;q=0.9", "en"),  # a language we don't have: English
        ("de-DE,de;q=0.9,pl;q=0.8", "pl"),  # ... unless Polish is among the browser's choices
    ],
)
def test_then_the_browser_language_decides(client, header, expected):
    response = client.get(reverse("account_login"), HTTP_ACCEPT_LANGUAGE=header)

    assert _language(response) == expected


@pytest.mark.django_db
def test_the_cookie_beats_the_browser_language(client):
    client.cookies[COOKIE] = "pl"

    assert _language(client.get(reverse("account_login"), HTTP_ACCEPT_LANGUAGE="en")) == "pl"


@pytest.mark.django_db
def test_the_accounts_language_beats_cookie_and_browser(client, user):
    _set_account_language(user, "pl")
    client.force_login(user)
    client.cookies[COOKIE] = "en"

    response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="en")

    assert _language(response) == "pl"
    assert response.cookies[COOKIE].value == "pl"  # the cookie follows the account


@pytest.mark.django_db
def test_an_account_without_a_language_uses_the_cookie(client, user):
    client.force_login(user)
    client.cookies[COOKIE] = "pl"

    response = client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="en")

    assert _language(response) == "pl"
    assert COOKIE not in response.cookies  # nothing to copy from the account


@pytest.mark.django_db
def test_reading_the_accounts_language_never_creates_settings(user):
    assert account_language(user) == ""
    assert not UserSettings.objects.exists()


# --- the PL · EN switcher -----------------------------------------------------------------


@pytest.mark.django_db
def test_the_switcher_sets_a_long_lived_cookie_and_goes_back(client):
    response = client.post(reverse("set_language"), {"language": "pl", "next": "/accounts/signup/"})

    assert response.status_code == 302
    assert response.url == "/accounts/signup/"
    assert response.cookies[COOKIE].value == "pl"
    assert response.cookies[COOKIE]["max-age"] == 365 * 24 * 60 * 60
    assert _language(client.get("/accounts/signup/")) == "pl"


@pytest.mark.django_db
def test_the_switcher_saves_the_choice_on_the_account(client, user):
    client.force_login(user)

    client.post(reverse("set_language"), {"language": "pl", "next": "/"})

    assert UserSettings.objects.get(user=user).language == "pl"
    assert _language(client.get(reverse("home"))) == "pl"


@pytest.mark.django_db
def test_the_switcher_ignores_unknown_languages_and_other_sites(client, user):
    client.force_login(user)

    response = client.post(
        reverse("set_language"), {"language": "de", "next": "https://evil.example/"}
    )

    assert response.url == "/"
    assert COOKIE not in response.cookies
    assert not UserSettings.objects.filter(user=user).exclude(language="").exists()


@pytest.mark.django_db
def test_the_switcher_only_accepts_post(client):
    assert client.get(reverse("set_language")).status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["account_login", "account_signup", "account_reset_password"])
def test_the_switcher_is_in_the_footer_before_logging_in(client, url_name):
    content = client.get(reverse(url_name)).content.decode()

    assert SWITCHER in content
    assert 'name="language" value="pl"' in content
    assert 'name="language" value="en"' in content


@pytest.mark.django_db
def test_the_switcher_is_hidden_only_while_a_workout_is_open(client, user, make_workout, bench):
    finished = make_workout(user, {bench: [(60, 8)]}, days_ago=2)
    workout = make_workout(user, {bench: [(60, 8)]}, days_ago=0, finished=False)
    client.force_login(user)
    logged_set = workout.sets.get()

    # The reload would lose the rest timer's screen and inputs typed but not logged.
    assert (
        SWITCHER
        not in client.get(reverse("workouts:workout_detail", args=[workout.pk])).content.decode()
    )
    assert (
        SWITCHER
        not in client.get(reverse("workouts:set_update", args=[logged_set.pk])).content.decode()
    )
    assert (
        SWITCHER
        in client.get(reverse("workouts:workout_detail", args=[finished.pk])).content.decode()
    )
    assert SWITCHER in client.get(reverse("home")).content.decode()


# --- Settings -------------------------------------------------------------------------------


@pytest.mark.django_db
def test_settings_offer_only_polish_and_english_with_the_current_one_chosen(client, user):
    client.force_login(user)

    content = client.get(reverse("settings")).content.decode()

    radios = re.findall(r'<input type="radio" name="language" value="(\w+)"[^>]*>', content)
    assert radios == ["pl", "en"]
    assert re.search(r'name="language" value="en"[^>]*checked', content)  # the page is English


@pytest.mark.django_db
def test_choosing_a_language_in_settings_saves_it_and_switches_at_once(client, user):
    client.force_login(user)

    response = client.post(
        reverse("settings"),
        {"language": "pl", "effort_scale": "simple", "ios_shortcut_name": "LiftLog Rest"},
        follow=True,
    )

    assert UserSettings.objects.get(user=user).language == "pl"
    assert client.cookies[COOKIE].value == "pl"
    assert _language(response) == "pl"
    assert "Ustawienia zapisane." in response.content.decode()


# --- signing up and logging in ----------------------------------------------------------------


@pytest.mark.django_db
def test_the_language_someone_signs_up_in_is_saved_on_the_account(client, mailoutbox):
    client.cookies[COOKIE] = "pl"

    client.post(
        reverse("account_signup"),
        {"email": "ania@example.com", "password1": PASSWORD, "password2": PASSWORD},
    )

    assert UserSettings.objects.get(user__email="ania@example.com").language == "pl"


@pytest.mark.django_db
def test_logging_in_on_a_new_device_switches_to_the_accounts_language(client):
    _verified_user("pl")

    response = _log_in(client, HTTP_ACCEPT_LANGUAGE="en")

    assert response.cookies[COOKIE].value == "pl"
    home = client.get(response.url, HTTP_ACCEPT_LANGUAGE="en")
    assert _language(home) == "pl"
    assert "Zalogowano jako ania." in home.content.decode()  # even allauth's message


@pytest.mark.django_db
def test_the_language_stays_after_logging_out(client):
    _verified_user("pl")
    _log_in(client, HTTP_ACCEPT_LANGUAGE="en")

    client.post(reverse("account_logout"))

    assert _language(client.get(reverse("account_login"), HTTP_ACCEPT_LANGUAGE="en")) == "pl"


# --- key pages in both languages -----------------------------------------------------------------

PAGES = {
    "en": {
        "home": ["Workout in progress", "Resume workout"],
        "plans:plan_list": ["No plans yet.", "Create your first plan"],
        "exercises:exercise_list": ["All muscles", "All equipment"],
        "settings": ["Rating your sets", "Save settings"],
        "workout": ["Finish workout", "Log set 2", "Last time", "60 × 8"],
    },
    "pl": {
        "home": ["Trening w toku", "Wróć do treningu"],
        "plans:plan_list": ["Nie masz jeszcze planów.", "Utwórz pierwszy plan"],
        "exercises:exercise_list": ["Wszystkie mięśnie", "Każdy sprzęt"],
        "settings": ["Ocena serii", "Zapisz ustawienia"],
        "workout": ["Zakończ trening", "Zapisz serię 2", "Ostatnio", "60 × 8"],
    },
}


@pytest.mark.django_db
@pytest.mark.parametrize("language", ["en", "pl"])
def test_key_pages_in_both_languages(client, user, make_workout, bench, language):
    workout = make_workout(user, {bench: [(60, 8)]}, days_ago=0, finished=False)
    client.force_login(user)
    client.cookies[COOKIE] = language

    for page, texts in PAGES[language].items():
        if page == "workout":
            url = reverse("workouts:workout_detail", args=[workout.pk])
        else:
            url = reverse(page)
        response = client.get(url)
        content = response.content.decode()
        assert _language(response) == language, page
        assert f'<html lang="{language}">' in content, page
        for text in texts:
            assert text in content, (page, text)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "language, texts",
    [
        ("en", ["Log in", "Forgot password?", "Create an account"]),
        ("pl", ["Zaloguj się", "Nie pamiętasz hasła?", "Załóż konto"]),
    ],
)
def test_the_login_page_in_both_languages(client, language, texts):
    client.cookies[COOKIE] = language

    content = client.get(reverse("account_login")).content.decode()

    for text in texts:
        assert text in content
