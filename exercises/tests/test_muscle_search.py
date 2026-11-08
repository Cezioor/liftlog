"""Searching by muscle and in everyday words: "ćwiczenie na smithie na dupę".

Muscle words (formal, colloquial, English) filter like equipment words, filler words are
ignored, and a muscle + equipment search suggests the exercises that could also be done
with that equipment. The library below copies the real data that matters.
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


def _target(words):
    return parse_query(words).target


# --- parsing --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query, words, equipment, muscle",
    [
        ("ćwiczenie na smithie na dupę", [], "smith", "pośladki"),
        ("glute exercises smith", [], "smith", "pośladki"),
        ("exercises for the butt with dumbbells", ["the"], "dumbbell", "pośladki"),
        ("klata hantle", [], "dumbbell", "klata"),
        ("bicki wyciąg", [], "cable", "biceps"),
        ("na tyłek", [], "", "pośladki"),
        ("jakieś ćwiczenie na kaloryfer", [], "", "brzuch"),
        ("tył uda", [], "", "dwugłowe"),
        ("uda", [], "", "uda"),
        ("nogi", [], "", "nogi"),
        ("kaptury hantle", [], "dumbbell", "kaptury"),
        ("bez sprzętu na plecy", [], "bodyweight", "plecy"),
        ("back squat", ["squat"], "", "plecy"),
        # Anatomical names and other forms of a word (compared by stem).
        ("najszerszy grzbietu", [], "", "najszerszy grzbietu"),
        ("mięsień najszerszego grzbietu", [], "", "najszerszy grzbietu"),
        ("trapezowy", [], "", "czworoboczny"),
        ("mięśnia czworobocznego", [], "", "czworoboczny"),
        ("czworogłowych", [], "", "uda + czworogłowy uda"),  # two entries, both the quads
        ("rozciąganie dołu podkolanowego", [], "", "dół podkolanowy"),  # + category
        ("dwugłowe i łydki", [], "", "dwugłowe + łydki"),
    ],
)
def test_parse_query_finds_muscles_equipment_and_drops_fillers(query, words, equipment, muscle):
    parsed = parse_query(query)

    target = parsed.target.name if parsed.target else ""
    assert (parsed.words, parsed.equipment, target) == (words, equipment, muscle)


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

    suggestions = equipment_suggestions(user, _target("klata"), "dumbbell")

    assert [s.base for s in suggestions] == [incline]
    # Barbell Bench Press is left out: "Dumbbell Bench Press" already exists.


@pytest.mark.django_db
def test_smith_suggestions_need_a_barbell_version(user, library):
    _exercise("Hammer Curl", "biceps", "dumbbell", primary=["biceps"])
    curl = _exercise("Barbell Curl", "biceps", "barbell", primary=["biceps"])

    assert [s.base for s in equipment_suggestions(user, _target("bicki"), "smith")] == [curl]


@pytest.mark.django_db
def test_no_suggestions_for_olympic_lifts_or_equipment_specific_moves(user, library):
    _exercise("Power Clean", "full_body", "barbell", primary=["glutes"])

    # Every other glute exercise already has a Smith version.
    assert equipment_suggestions(user, _target("pośladki"), "smith") == []
    assert equipment_suggestions(user, _target("klata"), "machine") == []


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


# --- anatomical names, smaller muscles, regions -------------------------------------------------


@pytest.fixture
def anatomy(db):
    return {
        "hamstring_stretch": _exercise(
            "90/90 Hamstring", "hamstrings", "bodyweight", "prostowanie nogi 90/90 leżąc",
            ["hamstrings"], category="mobility",
        ),
        "calf_stretch": _exercise(
            "Calf Stretch Hands Against Wall", "calves", "other", "rozciąganie łydki przy ścianie",
            ["calves"], category="mobility",
        ),
        "leg_curl": _exercise(
            "Lying Leg Curl", "hamstrings", "machine", "uginanie nóg leżąc", ["hamstrings"]
        ),
        "lat_stretch": _exercise(
            "One Arm Against Wall", "back", "other", "rozciąganie najszerszego przy ścianie",
            ["lats"], category="mobility",
        ),
        "back_extension": _exercise(
            "Back Extension", "back", "bodyweight", "wyprosty tułowia", ["lower back"]
        ),
        "shrug": _exercise("Barbell Shrug", "back", "barbell", "szrugsy", ["traps"]),
        "face_pull": _exercise(
            "Face Pull", "shoulders", "cable", "przyciąganie liny do twarzy, tylne aktony",
            ["shoulders"],
        ),
        "lateral_raise": _exercise(
            "Lateral Raise", "shoulders", "dumbbell", "wznosy bokiem z hantlami", ["shoulders"]
        ),
        "hip_flexor": _exercise(
            "Kneeling Hip Flexor", "quads", "other", "rozciąganie zginaczy biodra w klęku",
            ["quadriceps"], category="mobility",
        ),
    }  # fmt: skip


@pytest.mark.django_db
def test_back_of_the_knee_finds_hamstring_and_calf_stretches(user, anatomy):
    names = _names(search_exercises(user, "rozciąganie dołu podkolanowego"))

    assert names == ["90/90 Hamstring", "Calf Stretch Hands Against Wall"]
    assert "Lying Leg Curl" in _names(search_exercises(user, "dół podkolanowy"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query, expected, not_expected",
    [
        ("najszerszy grzbietu", "One Arm Against Wall", "Back Extension"),
        ("rozciąganie najszerszego", "One Arm Against Wall", "Barbell Shrug"),
        ("trapezowy", "Barbell Shrug", "One Arm Against Wall"),
        ("czworoboczny", "Barbell Shrug", "Back Extension"),
        ("prostowniki grzbietu", "Back Extension", "Barbell Shrug"),
    ],
)
def test_a_muscle_of_the_back_is_not_the_whole_back(user, anatomy, query, expected, not_expected):
    names = _names(search_exercises(user, query))

    assert expected in names
    assert not_expected not in names


@pytest.mark.django_db
def test_keywords_bring_a_smaller_muscle_to_the_top(user, anatomy):
    """The data only knows "shoulders"; "tylne aktony" in a Polish name goes first."""
    names = _names(search_exercises(user, "tylne aktony"))

    assert names[0] == "Face Pull"
    assert "Lateral Raise" in names  # still a shoulder exercise, lower


@pytest.mark.django_db
def test_a_muscle_the_data_does_not_tag_is_found_by_its_keywords(user, anatomy):
    assert _names(search_exercises(user, "zginacze bioder")) == ["Kneeling Hip Flexor"]


@pytest.mark.django_db
def test_two_muscle_words_find_either_muscle(user, anatomy):
    names = _names(search_exercises(user, "dwugłowe i łydki"))

    assert {"90/90 Hamstring", "Calf Stretch Hands Against Wall", "Lying Leg Curl"} <= set(names)
    assert "Face Pull" not in names


@pytest.mark.django_db
def test_other_forms_of_a_word_in_a_name_are_found(user, anatomy):
    """ "zginacze" is in the name as "zginaczy": words are compared by their stem."""
    assert "Kneeling Hip Flexor" in _names(search_exercises(user, "rozciąganie zginacze"))


# --- every possible variant, with helping muscles and "Show more" ------------------------------


@pytest.mark.django_db
def test_smith_suggestions_include_compound_lifts_for_a_helping_muscle(user, library):
    """ "na smithie na dupę": squats and deadlifts with a barbell work the glutes too."""
    deficit = _exercise(
        "Deficit Deadlift",
        "back",
        "barbell",
        primary=["lower back"],
        secondary=["glutes"],
        mechanic="compound",
    )
    _exercise(
        "Barbell Rollout from Bench",
        "core",
        "barbell",
        primary=["abdominals"],
        secondary=["glutes"],
        mechanic="compound",
    )  # ab exercise: glutes only help, not suggested
    _exercise(
        "Clean and Press",
        "shoulders",
        "barbell",
        primary=["shoulders"],
        secondary=["glutes"],
        mechanic="compound",
    )  # an Olympic lift, even if the data says "strength"
    _exercise(
        "Board Press",
        "triceps",
        "barbell",
        primary=["triceps"],
        secondary=["glutes"],
        mechanic="compound",
    )  # a barbell set-up

    suggestions = equipment_suggestions(user, _target("pośladki"), "smith")

    assert [s.base for s in suggestions] == [deficit]  # fmt: skip


@pytest.mark.django_db
def test_suggestions_list_the_main_muscle_before_helping_ones(user, library):
    for name in ("Barbell Lunge", "Barbell Glute March"):
        _exercise(name, "glutes", "barbell", primary=["glutes"], mechanic="compound")
    _exercise(
        "Deficit Deadlift",
        "back",
        "barbell",
        primary=["lower back"],
        secondary=["glutes"],
        mechanic="compound",
    )

    names = [s.base.name for s in equipment_suggestions(user, _target("pośladki"), "smith")]

    assert names == ["Barbell Glute March", "Barbell Lunge", "Deficit Deadlift"]


@pytest.mark.django_db
def test_more_than_ten_suggestions_go_behind_show_more(client, user, library):
    client.force_login(user)
    for number in range(12):
        _exercise(f"Barbell Glute Move {number:02}", "glutes", "barbell", primary=["glutes"])

    content = client.get(
        reverse("exercises:exercise_list"), {"q": "na smithie na dupę"}, **HTMX_RESULTS
    ).content.decode()

    assert content.count("Add variant: «Glute Move") == 12
    assert "Show 2 more" in content
    assert (
        content.index("Glute Move 09")
        < content.index("Show 2 more")
        < content.index("Glute Move 10")
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query, trains_it, only_position",
    [
        ("kolano", ("Leg Extensions", "quads", ["quadriceps"]), "przyciąganie kolan do klatki"),
        ("stopa", ("Standing Calf Raise", "calves", ["calves"]), "brzuszki ze stopami na ławce"),
        ("kark", ("Neck Flexion", "neck", ["neck"]), "przysiad ze sztangą na karku"),
    ],
)
def test_a_body_part_that_only_tells_the_position_does_not_go_first(
    user, query, trains_it, only_position
):
    """ "kolan" in "przyciąganie kolan do klatki" is where the knees go, not what is trained."""
    name, group, muscles = trains_it
    _exercise(name, group, "machine", primary=muscles)
    _exercise("Position Exercise", "core", "bodyweight", only_position, ["abdominals"])

    names = _names(search_exercises(user, query))

    assert names.index(name) < names.index("Position Exercise")


@pytest.mark.django_db
def test_a_query_describing_an_exercise_puts_it_first(user):
    """With a movement word, all the body words in a name point at that exercise."""
    _exercise(
        "Kettlebell Sumo High Pull",
        "back",
        "kettlebell",
        "przyciąganie kettlebell do barków",
        ["traps"],
        ["quadriceps", "hamstrings"],
    )
    _exercise("Leg Pull-In", "core", "bodyweight", "przyciąganie kolan do klatki leżąc")

    names = _names(search_exercises(user, "przyciąganie kolan do klatki"))

    assert names[0] == "Leg Pull-In"


@pytest.mark.django_db
def test_knee_finds_knee_circles_first(user):
    """Hip circles move the knee in a circle too, but their names say "kółka kolanem"."""
    _exercise(
        "Hip Circles (prone)",
        "glutes",
        "bodyweight",
        "krążenia biodra w klęku podpartym, kółka kolanem w klęku",
        ["abductors"],
    )
    _exercise("Knee Circles", "calves", "bodyweight", "krążenia kolan", ["calves"], ["quadriceps"])
    _exercise("Leg Extensions", "quads", "machine", "prostowanie nóg na maszynie", ["quadriceps"])

    assert _names(search_exercises(user, "kolano"))[0] == "Knee Circles"
