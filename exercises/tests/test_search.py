import pytest
from django.core.management import call_command
from django.urls import reverse

from exercises.models import Exercise
from exercises.seed_data import ALIASES, EXERCISES
from exercises.services import find_by_name, search_exercises
from exercises.text import normalize


@pytest.fixture
def library(db):
    call_command("seed_exercises")


def _names(queryset):
    return [e.name for e in queryset]


# --- normalize ------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Przysiad", "przysiad"),
        ("Zgięcia ramion", "zgiecia ramion"),
        ("ŁYDKI", "lydki"),
        ("Wyciskanie żołnierskie", "wyciskanie zolnierskie"),
        ("ćwiczenie źródło", "cwiczenie zrodlo"),
        ("Pull-up", "pull up"),
        ("  dużo   spacji ", "duzo spacji"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize(text, expected):
    assert normalize(text) == expected


# --- search_exercises -----------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["przysiad", "Przysiad", "PRZYSIAD", "przysiád"])
def test_search_ignores_case_and_accents(library, user, query):
    assert "Back Squat" in _names(search_exercises(user, query))


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["zgiecia", "zgięcia", "Zgięcia"])
def test_search_finds_polish_alias_without_diacritics(library, user, query):
    names = _names(search_exercises(user, query))

    assert "Barbell Curl" in names
    assert "Lying Leg Curl" in names


@pytest.mark.django_db
def test_search_handles_l_with_stroke(library, user):
    # "ł" doesn't decompose in Unicode, so it needs its own rule.
    assert "Standing Calf Raise" in _names(search_exercises(user, "lydki"))
    assert "Standing Calf Raise" in _names(search_exercises(user, "łydki"))


@pytest.mark.django_db
def test_search_finds_english_name(library, user):
    assert _names(search_exercises(user, "bench"))[0] in {
        "Barbell Bench Press",
        "Dumbbell Bench Press",
    }


@pytest.mark.django_db
def test_every_word_must_match(library, user):
    names = _names(search_exercises(user, "wyciskanie hantli skos"))

    assert names == ["Incline Dumbbell Press"]


@pytest.mark.django_db
def test_name_prefix_matches_come_first(library, user):
    names = _names(search_exercises(user, "deadlift"))

    assert names[0] == "Deadlift"
    assert "Romanian Deadlift" in names


@pytest.mark.django_db
def test_filters_by_muscle_group_and_equipment(library, user):
    names = _names(search_exercises(user, muscle_group="chest", equipment="dumbbell"))

    assert names == ["Dumbbell Bench Press", "Dumbbell Fly", "Incline Dumbbell Press"]


@pytest.mark.django_db
def test_invalid_filter_values_are_ignored(library, user):
    assert search_exercises(user, muscle_group="nope").count() == len(EXERCISES)


@pytest.mark.django_db
def test_search_never_returns_other_users_exercises(library, user, other_user):
    Exercise.objects.create(
        name="Przysiad sekretny", muscle_group="quads", equipment="other", owner=other_user
    )
    mine = Exercise.objects.create(
        name="Przysiad mój", muscle_group="quads", equipment="other", owner=user
    )

    names = _names(search_exercises(user, "przysiad"))

    assert mine.name in names
    assert "Przysiad sekretny" not in names


@pytest.mark.django_db
def test_search_text_updates_when_aliases_change(user):
    exercise = Exercise.objects.create(
        name="Sissy Squat", muscle_group="quads", equipment="bodyweight", owner=user
    )
    exercise.aliases = "przysiad syzyfowy"
    exercise.save()

    assert _names(search_exercises(user, "syzyfowy")) == ["Sissy Squat"]


def test_every_builtin_exercise_has_polish_aliases():
    names = {name for name, *_ in EXERCISES}

    assert set(ALIASES) == names
    assert all(ALIASES[name].strip() for name in names)


@pytest.mark.django_db
def test_find_by_name_ignores_case_and_diacritics(user):
    exercise = Exercise.objects.create(
        name="Łydki na suwnicy", muscle_group="calves", equipment="machine", owner=user
    )

    assert find_by_name(user, "łydki NA suwnicy") == exercise
    assert find_by_name(user, "lydki na suwnicy") == exercise
    assert find_by_name(user, "łydki") is None


@pytest.mark.django_db
def test_library_page_uses_the_same_search(client, library, user):
    client.force_login(user)

    response = client.get(reverse("exercises:exercise_list"), {"q": "zgiecia"})

    assert "Barbell Curl" in _names(response.context["results"])
