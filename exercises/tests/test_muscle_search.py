"""Searching by muscle and in everyday words: "ćwiczenie na smithie na dupę".

Muscle words (formal, colloquial, English) filter like equipment words, filler words are
ignored, and a muscle + equipment search suggests popular exercises that could also be
done with that equipment. The library below copies the real data that matters.
"""

import pytest
from django.urls import reverse

from exercises.models import Exercise, Movement
from exercises.services import equipment_suggestions, parse_query, search_exercises

HTMX_RESULTS = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "picker-results"}


def _exercise(name, group, equipment, aliases="", primary=(), secondary=(), **extra):
    return Exercise.objects.create(
        name=name,
        aliases=aliases,
        muscle_group=group,
        equipment=equipment,
        primary_muscles=list(primary),
        secondary_muscles=list(secondary),
        **extra,
    )


@pytest.fixture
def library(db):
    glutes = ["glutes"]
    squat_family = Movement.objects.create(name="Squat")
    return {
        "barbell_hip_thrust": _exercise(
            "Barbell Hip Thrust", "glutes", "barbell", "wypychanie bioder ze sztangą", glutes
        ),
        # The built-in Smith variants say "na suwnicy smitha", not "na smithie".
        "smith_hip_thrust": _exercise(
            "Smith Machine Hip Thrust", "glutes", "smith", "hip thrust na suwnicy smitha", glutes
        ),
        "smith_glute_bridge": _exercise(
            "Smith Machine Glute Bridge", "glutes", "smith", "mostek biodrowy na smithie", glutes
        ),
        "glute_bridge": _exercise(
            "Glute Bridge", "glutes", "bodyweight", "mostek biodrowy", glutes
        ),
        "adductor": _exercise(
            "Adductor", "glutes", "other", "rolowanie przywodzicieli", category="mobility"
        ),
        "back_squat": _exercise(
            "Back Squat", "quads", "barbell", "przysiad ze sztangą", ["quadriceps"], glutes
        ),
        "smith_squat": _exercise(
            "Smith Machine Squat", "quads", "smith", "przysiad na smithie", ["quadriceps"], glutes,
            movement=squat_family,
        ),
        "barbell_bench": _exercise(
            "Barbell Bench Press", "chest", "barbell", "wyciskanie sztangi na ławce płaskiej",
            ["chest"], mechanic="compound",
        ),
        "dumbbell_bench": _exercise(
            "Dumbbell Bench Press", "chest", "dumbbell", "wyciskanie hantli na ławce płaskiej",
            ["chest"], mechanic="compound",
        ),
        "cable_curl": _exercise(
            "Cable Curl", "biceps", "cable", "uginanie ramion na wyciągu", ["biceps"]
        ),
        "dumbbell_curl": _exercise(
            "Dumbbell Curl", "biceps", "dumbbell", "uginanie ramion z hantlami", ["biceps"]
        ),
        # Anatomical words that describe a position, not what the exercise trains.
        "leg_pull_in": _exercise(
            "Leg Pull-In", "core", "bodyweight", "przyciąganie kolan do klatki leżąc"
        ),
        "lying_curl": _exercise(
            "Lying Supine Dumbbell Curl", "biceps", "dumbbell", "uginanie hantli leżąc na plecach"
        ),
        "olympic_squat": _exercise(
            "Olympic Squat", "full_body", "barbell", "przysiad olimpijski, sztanga na karku"
        ),
        "quad_stretch": _exercise(
            "On Your Side Quad Stretch", "quads", "other", "pięta do pośladka leżąc bokiem",
            category="mobility",
        ),
    }  # fmt: skip


def _names(results):
    return [e.name for e in results]


# --- parsing --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query, words, equipment, muscle",
    [
        ("ćwiczenie na smithie na dupę", [], "smith", "glutes"),
        ("glute exercises smith", [], "smith", "glutes"),
        ("exercises for the butt with dumbbells", ["the"], "dumbbell", "glutes"),
        ("klata hantle", [], "dumbbell", "chest"),
        ("bicki wyciąg", [], "cable", "biceps"),
        ("na tyłek", [], "", "glutes"),
        ("jakieś ćwiczenie na kaloryfer", [], "", "core"),
        ("tył uda", [], "", "hamstrings"),
        ("uda", [], "", "quads"),
        ("nogi", [], "", "legs"),
        ("kaptury hantle", [], "dumbbell", "traps"),
        ("bez sprzętu na plecy", [], "bodyweight", "back"),
        ("back squat", ["squat"], "", "back"),
    ],
)
def test_parse_query_finds_muscles_equipment_and_drops_fillers(query, words, equipment, muscle):
    parsed = parse_query(query)

    assert (parsed.words, parsed.equipment, parsed.muscle) == (words, equipment, muscle)


# --- real queries ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["ćwiczenie na smithie na dupę", "glute exercises smith"])
def test_muscle_and_equipment_filter_together(user, library, query):
    names = _names(search_exercises(user, query))

    assert names[:2] == ["Smith Machine Glute Bridge", "Smith Machine Hip Thrust"]
    assert "Smith Machine Squat" in names  # glutes as a helping muscle, lower down
    assert "Barbell Hip Thrust" not in names


@pytest.mark.django_db
def test_hip_thrust_na_smithie(user, library):
    assert _names(search_exercises(user, "hip thrust na smithie")) == ["Smith Machine Hip Thrust"]


@pytest.mark.django_db
def test_na_tylek_shows_main_muscle_first_then_helping_muscle(user, library):
    names = _names(search_exercises(user, "na tyłek"))

    # Popular ones first (Barbell Hip Thrust, Glute Bridge are among the 65 common ones),
    # stretching after the exercises that train the muscle, squats (helping) lower.
    assert names[:2] == ["Barbell Hip Thrust", "Glute Bridge"]
    assert names.index("Adductor") > names.index("Smith Machine Hip Thrust")
    assert names.index("Back Squat") > names.index("Adductor")
    assert "Dumbbell Bench Press" not in names


@pytest.mark.django_db
def test_klata_hantle(user, library):
    names = _names(search_exercises(user, "klata hantle"))

    assert "Dumbbell Bench Press" in names
    assert "Barbell Bench Press" not in names


@pytest.mark.django_db
def test_bicki_wyciag(user, library):
    names = _names(search_exercises(user, "bicki wyciąg"))

    assert "Cable Curl" in names
    assert "Dumbbell Curl" not in names


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query, exercise",
    [
        ("przyciąganie kolan do klatki", "Leg Pull-In"),
        ("uginanie hantli leżąc na plecach", "Lying Supine Dumbbell Curl"),
        ("sztanga na karku", "Olympic Squat"),
        ("pięta do pośladka", "On Your Side Quad Stretch"),
    ],
)
def test_muscle_words_that_describe_a_position_still_find_the_exercise(
    user, library, query, exercise
):
    """ "klatki" in "przyciąganie kolan do klatki" is not about the chest: the word in the
    name still counts, like an equipment word does."""
    assert exercise in _names(search_exercises(user, query))


@pytest.mark.django_db
def test_a_name_starting_with_a_muscle_word_still_comes_first(user, library):
    assert _names(search_exercises(user, "back squat"))[0] == "Back Squat"
    assert _names(search_exercises(user, "glute bridge"))[0] == "Glute Bridge"


# --- "You can also do these on the Smith machine" ---------------------------------------------


@pytest.mark.django_db
def test_suggests_popular_exercises_without_a_version_with_that_equipment(user, library):
    # Dumbbells fit the chest: two built-in compound chest exercises use them.
    _exercise("Dumbbell Floor Press", "chest", "dumbbell", primary=["chest"], mechanic="compound")
    incline = _exercise(
        "Incline Barbell Bench Press", "chest", "barbell", primary=["chest"], mechanic="compound"
    )

    suggestions = equipment_suggestions(user, "chest", "dumbbell")

    assert [s.base for s in suggestions] == [incline]
    # Barbell Bench Press is left out: "Dumbbell Bench Press" already exists.


@pytest.mark.django_db
def test_smith_suggestions_need_a_barbell_version(user, library):
    _exercise("Hammer Curl", "biceps", "dumbbell", primary=["biceps"])
    curl = _exercise("Barbell Curl", "biceps", "barbell", primary=["biceps"])

    assert [s.base for s in equipment_suggestions(user, "biceps", "smith")] == [curl]


@pytest.mark.django_db
def test_no_suggestions_for_olympic_lifts_or_equipment_specific_moves(user, library):
    _exercise("Power Clean", "full_body", "barbell", primary=["glutes"])

    assert equipment_suggestions(user, "glutes", "smith") == []  # the rest has a Smith version
    assert equipment_suggestions(user, "chest", "machine") == []


@pytest.mark.django_db
def test_suggestions_show_under_the_results_and_disappear_when_empty(client, user, library):
    client.force_login(user)
    _exercise("Dumbbell Floor Press", "chest", "dumbbell", primary=["chest"], mechanic="compound")
    _exercise(
        "Incline Barbell Bench Press", "chest", "barbell", primary=["chest"], mechanic="compound"
    )
    url = reverse("exercises:exercise_list")

    content = client.get(url, {"q": "klata hantle"}, **HTMX_RESULTS).content.decode()
    assert "You can also do these with dumbbells" in content
    assert "Add variant: «Incline Bench Press» — Dumbbell" in content

    empty = client.get(url, {"q": "ćwiczenie na smithie na dupę"}, **HTMX_RESULTS)
    assert "You can also do these" not in empty.content.decode()


@pytest.mark.django_db
def test_suggestion_heading_is_polish_on_polish_pages(client, user, library):
    client.force_login(user)
    client.cookies["django_language"] = "pl"
    _exercise("Dumbbell Floor Press", "chest", "dumbbell", primary=["chest"], mechanic="compound")
    _exercise(
        "Incline Barbell Bench Press", "chest", "barbell", primary=["chest"], mechanic="compound"
    )

    content = client.get(
        reverse("exercises:exercise_list"), {"q": "klata hantle"}, **HTMX_RESULTS
    ).content.decode()

    assert "Możesz zrobić też z hantlami" in content
