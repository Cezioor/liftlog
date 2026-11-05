"""Smith machine equipment, equipment words in search, exercise variants."""

import pytest
from django.core.management import call_command
from django.urls import reverse

from exercises.models import Equipment, Exercise
from exercises.services import (
    create_variant,
    parse_query,
    search_exercises,
    stem,
    variant_suggestion,
)
from exercises.smith_variants import SMITH_VARIANTS
from workouts.services import personal_records

HTMX_RESULTS = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "picker-results"}


def _names(queryset):
    return [e.name for e in queryset]


@pytest.fixture
def step_up(db):
    return Exercise.objects.create(
        name="Step-up", aliases="wejścia na skrzynię", muscle_group="quads",
        equipment="dumbbell", measurement="weight_reps", is_unilateral=True,
        primary_muscles=["quadriceps", "glutes"], secondary_muscles=["hamstrings"],
        level="beginner", mechanic="compound", instructions=["Step up.", "Step down."],
        images=["Dumbbell_Step_Ups/0.jpg", "Dumbbell_Step_Ups/1.jpg"],
    )  # fmt: skip


@pytest.fixture
def smith_squat(db):
    return Exercise.objects.create(
        name="Smith Machine Squat", muscle_group="quads", equipment="smith"
    )


@pytest.fixture
def leg_press(db):
    return Exercise.objects.create(
        name="Leg Press", aliases="wypychanie nóg na suwnicy", muscle_group="quads",
        equipment="machine",
    )  # fmt: skip


# --- search: hyphens, spaces, plurals -------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query", ["step up", "step-up", "stepup", "step ups", "Step-Ups", "STEP UPS"]
)
def test_hyphens_spaces_and_plurals_do_not_matter(user, step_up, query):
    assert _names(search_exercises(user, query)) == ["Step-up"]


@pytest.mark.django_db
def test_plural_name_found_by_singular_and_plural(user):
    Exercise.objects.create(name="Dumbbell Lunges", muscle_group="quads", equipment="dumbbell")

    for query in ("lunge", "lunges", "dumbbell lunge"):
        assert "Dumbbell Lunges" in _names(search_exercises(user, query))


@pytest.mark.parametrize(
    "word, expected",
    [("ups", "up"), ("presses", "press"), ("press", "press"), ("crunches", "crunch"),
     ("flies", "fly"), ("squats", "squat"), ("biceps", "bicep"), ("us", "us")],
)  # fmt: skip
def test_stem(word, expected):
    assert stem(word) == expected


# --- equipment words ------------------------------------------------------------------


@pytest.mark.parametrize(
    "query, words, equipment",
    [
        ("step up smith", ["step", "up"], "smith"),
        ("step-ups Smith machine", ["step", "up"], "smith"),
        ("przysiad na suwnicy", ["przysiad", "na"], "smith"),
        ("przysiad z hantlami", ["przysiad", "z"], "dumbbell"),
        ("wiosłowanie sztangą", ["wioslowanie"], "barbell"),
        ("kettlebell swing", ["swing"], "kettlebell"),
        ("prostowanie ramion wyciąg", ["prostowanie", "ramion"], "cable"),
        ("face pull linka", ["face", "pull"], "cable"),
        ("odwodzenie gumy", ["odwodzenie"], "band"),
        ("wyprosty maszyna", ["wyprosty"], "machine"),
        ("dumbbells", [], "dumbbell"),
        ("bench press", ["bench", "press"], ""),
    ],
)
def test_parse_query_finds_equipment_words(query, words, equipment):
    parsed = parse_query(query)

    assert (parsed.words, parsed.equipment) == (words, equipment)


@pytest.mark.django_db
def test_equipment_word_filters_results(user, step_up, smith_squat):
    Exercise.objects.create(name="Back Squat", muscle_group="quads", equipment="barbell")

    assert _names(search_exercises(user, "squat smith")) == ["Smith Machine Squat"]
    assert _names(search_exercises(user, "przysiad suwnica")) == []  # no Polish name here
    assert _names(search_exercises(user, "squat sztanga")) == ["Back Squat"]


@pytest.mark.django_db
def test_equipment_word_also_matches_names(user, smith_squat, leg_press):
    # "suwnica" is Smith machine, but the leg press is called "…na suwnicy" in Polish.
    assert _names(search_exercises(user, "suwnica")) == ["Leg Press", "Smith Machine Squat"]


# --- variant suggestion -----------------------------------------------------------------


@pytest.mark.django_db
def test_suggests_a_variant_when_movement_exists_without_that_equipment(user, step_up):
    suggestion = variant_suggestion(user, "step up smith")

    assert suggestion.base == step_up
    assert suggestion.equipment == "smith"
    assert suggestion.equipment_label == "Smith machine"


@pytest.mark.django_db
def test_no_suggestion_when_the_equipment_version_exists(user, step_up):
    Exercise.objects.create(name="Smith Machine Step-up", muscle_group="quads", equipment="smith")

    assert variant_suggestion(user, "step up smith") is None


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["step up", "smith", "zzz smith"])
def test_no_suggestion_without_both_movement_and_equipment(user, step_up, query):
    assert variant_suggestion(user, query) is None


@pytest.mark.django_db
def test_suggestion_points_to_the_original_not_to_a_variant(user, step_up):
    kettlebell = create_variant(user, step_up, "kettlebell")
    Exercise.objects.filter(pk=step_up.pk).update(name="Zz Step-up")  # variant sorts first

    assert variant_suggestion(user, "step up smith").base.pk == kettlebell.variant_of_id


# --- creating a variant -------------------------------------------------------------------


@pytest.mark.django_db
def test_variant_copies_the_movement_and_changes_the_equipment(user, step_up):
    variant = create_variant(user, step_up, "smith")

    assert variant.name == "Step-up (Smith machine)"
    assert (variant.owner, variant.variant_of, variant.equipment) == (user, step_up, "smith")
    for field in ("muscle_group", "measurement", "category", "is_unilateral", "level",
                  "mechanic", "primary_muscles", "secondary_muscles", "instructions",
                  "images", "aliases"):  # fmt: skip
        assert getattr(variant, field) == getattr(step_up, field), field
    assert step_up.progression_step_kg == 2  # dumbbell step
    assert variant.progression_step_kg == 5  # Smith machine, legs


@pytest.mark.django_db
def test_creating_the_same_variant_twice_reuses_it(user, step_up):
    assert create_variant(user, step_up, "smith") == create_variant(user, step_up, "smith")
    assert Exercise.objects.filter(variant_of=step_up).count() == 1


@pytest.mark.django_db
def test_variant_has_its_own_history_and_records(user, make_workout, step_up):
    variant = create_variant(user, step_up, "smith")
    make_workout(user, {step_up: [(20, 10)], variant: [(60, 8)]})

    assert personal_records(user, step_up)[1].workout_set.weight_kg == 20
    assert personal_records(user, variant)[1].workout_set.weight_kg == 60


# --- screens ---------------------------------------------------------------------------


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def picker_url(user, make_workout):
    workout = make_workout(user, days_ago=0, finished=False)
    return reverse("workouts:add_exercise", args=[workout.pk])


@pytest.mark.django_db
def test_picker_shows_add_variant_on_top(logged_in, picker_url, step_up):
    content = logged_in.get(picker_url, {"q": "step up smith"}, **HTMX_RESULTS).content.decode()

    assert "+ Add variant: «Step-up» — Smith machine" in content
    assert content.index("Add variant") < content.index("Results")


@pytest.mark.django_db
def test_tapping_add_variant_creates_and_picks_it(logged_in, user, picker_url, step_up):
    response = logged_in.post(
        reverse("exercises:exercise_variant_create", args=[step_up.pk]),
        {"equipment": "smith", "next": f"{picker_url}?exercise="},
    )

    variant = Exercise.objects.get(variant_of=step_up)
    assert variant.owner == user
    assert response.url == f"{picker_url}?exercise={variant.pk}"
    final = logged_in.get(response.url)
    assert final.url.endswith(f"?add={variant.pk}#ex-{variant.pk}")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data", [{"equipment": "laser"}, {"equipment": "smith", "next": "https://evil.example/"}]
)
def test_add_variant_rejects_bad_input(logged_in, picker_url, step_up, data):
    data = {"next": f"{picker_url}?exercise=", **data}

    response = logged_in.post(reverse("exercises:exercise_variant_create", args=[step_up.pk]), data)

    assert response.status_code == 400
    assert not Exercise.objects.filter(variant_of=step_up).exists()


@pytest.mark.django_db
def test_cannot_make_a_variant_of_another_users_exercise(logged_in, picker_url, other_user):
    theirs = Exercise.objects.create(
        name="Secret move", muscle_group="core", equipment="other", owner=other_user
    )

    response = logged_in.post(
        reverse("exercises:exercise_variant_create", args=[theirs.pk]),
        {"equipment": "smith", "next": f"{picker_url}?exercise="},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_add_my_own_comes_first_and_big_when_nothing_matches(logged_in, picker_url):
    content = logged_in.get(
        picker_url, {"q": "Zercher Kettlebell"}, **HTMX_RESULTS
    ).content.decode()

    assert "picker-add-prominent" in content
    assert "+ Add my own exercise: «Zercher Kettlebell»" in content
    assert content.index("Add my own") < content.index("No exercise matches")
    # The equipment word becomes the new exercise's equipment.
    assert 'name="equipment" value="kettlebell"' in content


@pytest.mark.django_db
def test_detail_pages_link_base_and_variants(logged_in, user, other_user, step_up):
    mine = create_variant(user, step_up, "smith")
    create_variant(other_user, step_up, "kettlebell")

    base_page = logged_in.get(reverse("exercises:exercise_detail", args=[step_up.pk]))
    variant_page = logged_in.get(reverse("exercises:exercise_detail", args=[mine.pk]))

    assert list(base_page.context["variants"]) == [mine]  # not the other user's
    assert "Step-up (Smith machine)" in base_page.content.decode()
    assert "Variant of" in variant_page.content.decode()


# --- data: Smith exercises from the import and the built-in variants ----------------------


@pytest.mark.django_db
def test_import_moves_the_20_smith_exercises_to_smith_machine():
    from exercises.free_db import import_dataset, load_dataset

    call_command("seed_exercises")
    import_dataset(load_dataset())

    smith = Exercise.objects.filter(owner=None, equipment=Equipment.SMITH)
    assert smith.count() == 20
    assert all("smith" in e.name.lower() for e in smith)
    assert not Exercise.objects.filter(name__icontains="smith").exclude(equipment="smith").exists()


@pytest.mark.django_db
def test_seed_smith_variants_links_them_to_their_bases():
    from exercises.free_db import import_dataset, load_dataset

    call_command("seed_exercises")
    import_dataset(load_dataset())
    call_command("seed_smith_variants")
    call_command("seed_smith_variants")  # safe to run again

    variants = Exercise.objects.filter(name__in=[v[0] for v in SMITH_VARIANTS], owner=None)
    assert len(SMITH_VARIANTS) == variants.count() == 30
    assert all(v.equipment == "smith" for v in variants)
    linked = variants.exclude(variant_of=None)
    expected_links = sum(1 for v in SMITH_VARIANTS if v[1])
    assert linked.count() == expected_links
    step = Exercise.objects.get(name="Smith Machine Step-up")
    assert step.variant_of.name == "Barbell Step Ups"
    assert step.images == step.variant_of.images
    assert step.is_unilateral
    # And "step up smith" now finds it instead of offering a new variant.
    from accounts.models import User

    user = User.objects.create_user(username="x")
    assert "Smith Machine Step-up" in _names(search_exercises(user, "step up smith"))
    assert variant_suggestion(user, "step up smith") is None


def test_smith_variant_data_is_valid():
    from exercises.models import Measurement, Muscle, MuscleGroup

    names = [v[0] for v in SMITH_VARIANTS]
    assert len(names) == len(set(names))
    for name, _, aliases, group, primary, secondary, measurement, _, steps in SMITH_VARIANTS:
        assert group in MuscleGroup.values, name
        assert set(primary + secondary) <= set(Muscle.values), name
        assert measurement in Measurement.values, name
        assert aliases and steps, name


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Barbell Step Ups", "Step Ups"),
        ("Smith Machine Squat", "Squat"),
        ("Dumbbell Bench Press", "Bench Press"),
        ("Step-up", "Step-up"),
        ("Barbell", "Barbell"),  # nothing would be left: unchanged
    ],
)
def test_movement_name_drops_equipment_words(name, expected):
    from exercises.services import movement_name

    assert movement_name(name) == expected


@pytest.mark.django_db
def test_suggestion_prefers_the_plainest_match_and_names_the_variant_cleanly(user):
    Exercise.objects.create(
        name="Step-up with Knee Raise", aliases="wejście z kolanem", muscle_group="quads",
        equipment="bodyweight",
    )  # fmt: skip
    barbell = Exercise.objects.create(
        name="Barbell Step Ups", muscle_group="quads", equipment="barbell"
    )

    suggestion = variant_suggestion(user, "step up kettlebell")
    variant = create_variant(user, suggestion.base, suggestion.equipment)

    assert suggestion.base == barbell
    assert suggestion.movement == "Step Ups"
    assert variant.name == "Step Ups (Kettlebell)"
