"""Numbers and plurals in Polish and English.

Visible text uses the language's decimal separator ("62,5" in Polish, display_kg), but
input values, data-* attributes, URLs and JS always get a dot (format_kg). Polish has
three plural forms that matter here: 1 seria, 2 serie, 5 serii.
"""

import re
from decimal import Decimal

import pytest
from django.conf import settings as django_settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ngettext

from exercises.models import Exercise
from workouts.models import WorkoutSet
from workouts.services import display_kg, format_kg, progression_hint, reps_text

COOKIE = django_settings.LANGUAGE_COOKIE_NAME


# --- display_kg / format_kg ---------------------------------------------------------------


@pytest.mark.parametrize(
    "value, polish, english",
    [
        ("60", "60", "60"),
        ("60.00", "60", "60"),
        ("62.5", "62,5", "62.5"),
        ("62.50", "62,5", "62.5"),
        ("61.25", "61,25", "61.25"),
        ("0.5", "0,5", "0.5"),
    ],
)
def test_display_kg_drops_trailing_zeros_and_uses_the_languages_separator(value, polish, english):
    with translation.override("pl"):
        assert display_kg(Decimal(value)) == polish
        assert format_kg(Decimal(value)) == english  # always a dot, for inputs and attributes
    with translation.override("en"):
        assert display_kg(Decimal(value)) == english


def test_display_kg_of_nothing_is_empty():
    assert display_kg(None) == ""


# --- plurals ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "count, sets, reps",
    [
        (1, "1 seria", "1 powtórzenie"),
        (2, "2 serie", "2 powtórzenia"),
        (4, "4 serie", "4 powtórzenia"),
        (5, "5 serii", "5 powtórzeń"),
        (12, "12 serii", "12 powtórzeń"),
        (22, "22 serie", "22 powtórzenia"),
        (25, "25 serii", "25 powtórzeń"),
    ],
)
def test_polish_plural_forms(count, sets, reps):
    with translation.override("pl"):
        assert ngettext("%(done)s set", "%(done)s sets", count) % {"done": count} == sets
        assert reps_text(count) == reps


def test_english_plurals():
    assert reps_text(1) == "1 rep"
    assert reps_text(8) == "8 reps"


# --- the workout screen in Polish ------------------------------------------------------------


@pytest.fixture
def polish_client(client, user):
    client.force_login(user)
    client.cookies[COOKIE] = "pl"
    return client


@pytest.mark.django_db
def test_polish_workout_screen_shows_commas_but_inputs_keep_dots(
    polish_client, user, make_workout, bench
):
    workout = make_workout(user, {bench: [(62.5, 8), (62.5, 8)]}, days_ago=0, finished=False)
    WorkoutSet.objects.filter(workout=workout).update(rir=Decimal("1.5"))

    content = polish_client.get(reverse("workouts:workout_detail", args=[workout.pk])).content
    content = content.decode()

    assert "62,5 × 8 · Ciężko" in content  # what you read
    assert "2 serie" in content
    # What the browser sends back and JS reads: the next set is pre-filled with a dot.
    assert re.search(r'name="weight_kg" value="62.5"', content)
    assert 'value="1.5"' in content  # the "Hard" rating button
    assert 'data-step="2.5"' in content
    assert 'data-rest="90"' in content
    assert not re.search(r'(value|data-[a-z-]+)="[^"]*\d,\d', content)  # no comma in attributes


@pytest.mark.django_db
def test_polish_progression_hint_uses_a_comma(bench):
    previous = [WorkoutSet(weight_kg=Decimal("60"), reps=12) for _ in range(3)]

    with translation.override("pl"):
        hint = progression_hint(bench, previous, rep_max=12)

    assert hint.weight_kg == Decimal("62.5")
    assert hint.message == "Ostatnio we wszystkich seriach 12 powtórzeń. Spróbuj 62,5 kg."


# --- typing a comma (Polish phone keyboards) ------------------------------------------------


@pytest.mark.django_db
def test_a_weight_typed_with_a_comma_is_saved_in_polish(polish_client, user, make_workout, bench):
    workout = make_workout(user, days_ago=0, finished=False)

    polish_client.post(
        reverse("workouts:set_create", args=[workout.pk, bench.pk]),
        {"weight_kg": "62,5", "reps": "8"},
    )

    assert WorkoutSet.objects.get(workout=workout).weight_kg == Decimal("62.5")


@pytest.mark.django_db
def test_a_progression_step_typed_with_a_comma_is_saved_in_polish(polish_client, user):
    polish_client.post(
        reverse("exercises:exercise_create"),
        {
            "name": "Moje wyciskanie",
            "muscle_group": "chest",
            "equipment": "dumbbell",
            "progression_step_kg": "1,25",
        },
    )

    assert Exercise.objects.get(owner=user).progression_step_kg == Decimal("1.25")
