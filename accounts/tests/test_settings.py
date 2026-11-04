import json
from urllib.parse import parse_qs, urlsplit

import pytest
from django.urls import reverse

from accounts.models import UserSettings
from accounts.services import get_user_settings, ios_shortcut_url
from plans.models import Plan, PlanDay, PlanExercise

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


# --- model and services ---------------------------------------------------


@pytest.mark.django_db
def test_settings_are_created_with_defaults_on_first_use(user):
    settings = get_user_settings(user)

    assert settings.ios_shortcut_enabled is False
    assert settings.ios_shortcut_name == "LiftLog Rest"
    assert settings.keep_screen_on is False
    assert settings.rest_end_sound is True
    assert get_user_settings(user) == settings  # not created twice
    assert UserSettings.objects.count() == 1


def test_ios_shortcut_url_encodes_everything():
    url = ios_shortcut_url(
        "LiftLog Rest", 90, "https://liftlog.onrender.com/workouts/7/?add=3#ex-3"
    )

    parts = urlsplit(url)
    assert (parts.scheme, parts.netloc, parts.path) == (
        "shortcuts",
        "x-callback-url",
        "/run-shortcut",
    )
    assert "LiftLog%20Rest" in url  # spaces as %20, which Shortcuts expects
    assert "https%3A%2F%2F" in url  # the return URL is fully encoded
    params = parse_qs(parts.query)
    assert params == {
        "name": ["LiftLog Rest"],
        "input": ["text"],
        "text": ["90"],
        "x-success": ["https://liftlog.onrender.com/workouts/7/?add=3#ex-3"],
    }


# --- settings page --------------------------------------------------------


@pytest.mark.django_db
def test_settings_page_requires_login(client):
    response = client.get(reverse("settings"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_settings_page_shows_form_and_shortcut_guide(logged_in):
    content = logged_in.get(reverse("settings")).content.decode()

    assert "iPhone Clock timer via Shortcuts" in content
    assert "Make the iPhone shortcut" in content
    assert "Shortcut Input" in content
    assert "seconds" in content


@pytest.mark.django_db
def test_save_settings(logged_in, user):
    response = logged_in.post(
        reverse("settings"),
        {
            "ios_shortcut_enabled": "on",
            "ios_shortcut_name": "  Gym rest  ",
            "keep_screen_on": "on",
        },
    )

    assert response.status_code == 302
    settings = get_user_settings(user)
    assert settings.ios_shortcut_enabled is True
    assert settings.ios_shortcut_name == "Gym rest"
    assert settings.keep_screen_on is True
    assert settings.rest_end_sound is False  # unchecked checkbox


@pytest.mark.django_db
def test_shortcut_needs_a_name(logged_in, user):
    response = logged_in.post(
        reverse("settings"), {"ios_shortcut_enabled": "on", "ios_shortcut_name": "   "}
    )

    assert response.status_code == 200
    assert response.context["form"].errors["ios_shortcut_name"]
    assert get_user_settings(user).ios_shortcut_enabled is False


@pytest.mark.django_db
def test_settings_page_only_changes_own_settings(client, user, other_user):
    get_user_settings(other_user)
    client.force_login(user)

    client.post(reverse("settings"), {"ios_shortcut_name": "Mine", "keep_screen_on": "on"})

    assert get_user_settings(user).keep_screen_on is True
    assert get_user_settings(other_user).keep_screen_on is False
    assert get_user_settings(other_user).ios_shortcut_name == "LiftLog Rest"


# --- effect on the workout screen -----------------------------------------


@pytest.fixture
def workout_with_bench(user, bench, make_workout):
    plan = Plan.objects.create(owner=user, name="PPL", is_active=True)
    day = PlanDay.objects.create(plan=plan, name="Push", order=1)
    PlanExercise.objects.create(day=day, exercise=bench, rest_seconds=150)
    return make_workout(user, plan_day=day, days_ago=0, finished=False)


def _log_set(client, workout, exercise):
    url = reverse("workouts:set_create", args=[workout.pk, exercise.pk])
    return client.post(url, {"weight_kg": "60", "reps": "10"}, **HTMX)


@pytest.mark.django_db
def test_rest_event_has_no_shortcut_by_default(logged_in, workout_with_bench, bench):
    response = _log_set(logged_in, workout_with_bench, bench)

    assert json.loads(response["HX-Trigger"]) == {"restStart": {"seconds": 150}}


@pytest.mark.django_db
def test_rest_event_includes_shortcut_url_when_enabled(logged_in, user, workout_with_bench, bench):
    settings = get_user_settings(user)
    settings.ios_shortcut_enabled = True
    settings.ios_shortcut_name = "Gym rest"
    settings.save()

    response = _log_set(logged_in, workout_with_bench, bench)

    rest = json.loads(response["HX-Trigger"])["restStart"]
    assert rest["seconds"] == 150
    params = parse_qs(urlsplit(rest["shortcutUrl"]).query)
    assert params["name"] == ["Gym rest"]
    assert params["text"] == ["150"]
    assert params["x-success"] == [
        f"http://testserver/workouts/{workout_with_bench.pk}/#ex-{bench.pk}"
    ]


@pytest.mark.django_db
def test_workout_page_passes_screen_and_sound_settings(logged_in, user, workout_with_bench):
    settings = get_user_settings(user)
    settings.keep_screen_on = True
    settings.rest_end_sound = False
    settings.save()

    content = logged_in.get(
        reverse("workouts:workout_detail", args=[workout_with_bench.pk])
    ).content.decode()

    assert 'data-keep-screen-on="1"' in content
    assert 'data-rest-sound="0"' in content
    assert 'id="rest-shortcut"' in content
