"""Filter chips of the exercise picker: only chips with results, the bar of chosen filters,
ways out of an empty result and "More filters" (Next up 5.7)."""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse

from exercises.models import Exercise
from exercises.picker import picker_response
from exercises.services import WARMUP, filter_options, search_exercises
from plans.models import Plan, PlanDay

HTMX = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "picker-results"}


@pytest.fixture
def zorro(user):
    """The user's own exercises, all found by "zorro" (no built-in has the word)."""
    rows = [
        ("Zorro curl", "biceps", "dumbbell", "beginner"),
        ("Zorro curl smith", "biceps", "smith", ""),
        ("Zorro rozgrzewka bicepsa", "biceps", "bodyweight", "beginner"),
        ("Zorro press", "chest", "smith", "intermediate"),
    ]
    for name, muscle, equipment, level in rows:
        Exercise.objects.create(
            name=name, muscle_group=muscle, equipment=equipment, level=level, owner=user
        )


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def library_url():
    return reverse("exercises:exercise_list")


def _row(context, name):
    rows = context["main_rows"] + context["more_rows"]
    return next(row for row in rows if row["name"] == name)


def _values(context, name):
    return [value for value, _label in _row(context, name)["choices"]]


def _params(url):
    return {key: values[0] for key, values in parse_qs(urlsplit(url).query).items()}


# --- the counting, without views -----------------------------------------------------


@pytest.mark.django_db
def test_each_count_is_the_number_of_results_that_chip_would_give(user, zorro):
    options = filter_options(user, "zorro", muscle_group="biceps")

    for value, count in options.counts["equipment"].items():
        assert count == search_exercises(user, "zorro", "biceps", equipment=value).count()
    assert options.counts["equipment"] == {"dumbbell": 1, "smith": 1, "bodyweight": 1}
    assert options.total == search_exercises(user, "zorro", "biceps").count() == 3


@pytest.mark.django_db
def test_a_rows_own_choice_is_left_out_so_it_can_be_changed(user, zorro):
    options = filter_options(user, "zorro", muscle_group="biceps", equipment="smith")

    # Chest is still offered in the muscle row (with Smith: "Zorro press").
    assert options.counts["muscle"] == {"biceps": 1, "chest": 1}
    # And the other equipment in its own row (with biceps).
    assert options.counts["equipment"] == {"dumbbell": 1, "smith": 1, "bodyweight": 1}


@pytest.mark.django_db
def test_warmup_is_counted_apart_from_the_categories(user, zorro):
    options = filter_options(user, "zorro")

    assert options.counts["category"] == {"strength": 4, WARMUP: 1}
    assert (
        options.counts["category"][WARMUP]
        == search_exercises(user, "zorro", category=WARMUP).count()
    )
    # Taking the type off counts every exercise once, not the warm-up twice.
    assert filter_options(user, "zorro", category=WARMUP).without("category") == 4


@pytest.mark.django_db
def test_without_a_level_counts_exercises_that_have_none(user):
    Exercise.objects.create(name="Qwerty lift", muscle_group="back", equipment="other", owner=user)

    options = filter_options(user, "qwerty", level="beginner")

    assert options.total == 0
    assert options.counts["level"] == {"": 1}
    assert options.without("level") == search_exercises(user, "qwerty").count() == 1


# --- the chips in the picker ---------------------------------------------------------


@pytest.mark.django_db
def test_chips_without_results_disappear(logged_in, library_url, zorro):
    context = logged_in.get(library_url, {"q": "zorro"}, **HTMX).context

    assert _values(context, "muscle") == ["chest", "biceps"]
    assert set(_values(context, "equipment")) == {"dumbbell", "smith", "bodyweight"}
    assert _values(context, "level") == ["beginner", "intermediate"]
    assert [v for v in _values(context, "category")] == ["strength", WARMUP]
    # "All …" chips are always there.
    content = logged_in.get(library_url, {"q": "zorro"}, **HTMX).content.decode()
    assert "All muscles" in content and "All equipment" in content
    assert 'value="kettlebell"' not in content


@pytest.mark.django_db
def test_chosen_chip_stays_even_with_no_results(logged_in, library_url, zorro):
    params = {"q": "zorro", "muscle": "chest", "equipment": "dumbbell"}

    context = logged_in.get(library_url, params, **HTMX).context

    assert context["results_count"] == 0
    assert "chest" in _values(context, "muscle")
    assert "dumbbell" in _values(context, "equipment")
    assert _row(context, "muscle")["chosen"] == "chest"
    content = logged_in.get(library_url, params, **HTMX).content.decode()
    assert 'name="equipment" value="dumbbell" checked' in content


@pytest.mark.django_db
def test_another_chip_in_the_same_row_can_be_chosen(logged_in, library_url, zorro):
    context = logged_in.get(library_url, {"q": "zorro", "muscle": "chest"}, **HTMX).context

    assert "biceps" in _values(context, "muscle")


@pytest.mark.django_db
def test_chips_come_with_the_results_out_of_band(logged_in, library_url, zorro):
    partial = logged_in.get(library_url, {"q": "zorro"}, **HTMX).content.decode()
    page = logged_in.get(library_url, {"q": "zorro"}).content.decode()

    assert '<div id="picker-filters" class="picker-filters" hx-swap-oob="true">' in partial
    assert page.count('id="picker-filters"') == 1
    assert "hx-swap-oob" not in page
    assert "js/picker.js" in page


# --- the bar of chosen filters -------------------------------------------------------


@pytest.mark.django_db
def test_no_bar_without_filters(logged_in, library_url, zorro):
    content = logged_in.get(library_url, {"q": "zorro"}, **HTMX).content.decode()

    assert "filter-bar" not in content
    assert "Clear filters" not in content


@pytest.mark.django_db
def test_bar_takes_off_one_filter_at_a_time(logged_in, library_url, zorro):
    params = {"q": "zorro", "muscle": "biceps", "equipment": "smith"}
    response = logged_in.get(library_url, params, **HTMX)
    chosen = response.context["chosen_filters"]

    assert [f["label"] for f in chosen] == ["Biceps", "Smith machine"]
    content = response.content.decode()
    assert "filter-bar" in content and "Clear filters" in content
    biceps_off = chosen[0]["remove_url"]
    assert _params(biceps_off) == {"q": "zorro", "equipment": "smith"}
    assert _params(response.context["clear_url"]) == {"q": "zorro"}

    after = logged_in.get(biceps_off, **HTMX).context
    assert (after["muscle"], after["equipment"]) == ("", "smith")
    assert after["results_count"] == 2


# --- ways out of an empty result -----------------------------------------------------


@pytest.mark.django_db
def test_empty_result_offers_each_filter_that_gives_results(logged_in, library_url, zorro):
    params = {"q": "zorro", "muscle": "biceps", "equipment": "smith", "category": WARMUP}
    response = logged_in.get(library_url, params, **HTMX)
    context = response.context

    assert context["results_count"] == 0
    # Without the muscle: Smith + warm-up gives nothing, so no button for it.
    hints = {f["label"]: f["without"] for f in context["way_out"]}
    assert hints == {"Smith machine": 1, "Warm-up": 1}
    content = response.content.decode()
    assert "Without “Smith machine”: 1 exercise" in content
    assert "Without “Warm-up”: 1 exercise" in content
    assert "Without “Biceps”" not in content
    # "Clear filters" only once: in the bar above the results, not under the hints.
    assert content.count("Clear filters") == 1
    assert "Clear filters" not in content.split('class="picker-way-out"', 1)[1]
    # Each number is what the button gives.
    for hint in context["way_out"]:
        after = logged_in.get(hint["remove_url"], **HTMX).context
        assert after["results_count"] == hint["without"]


@pytest.mark.django_db
def test_way_out_counts_exercises_without_a_level(logged_in, user, library_url):
    Exercise.objects.create(name="Qwerty lift", muscle_group="back", equipment="other", owner=user)

    context = logged_in.get(library_url, {"q": "qwerty", "level": "beginner"}, **HTMX).context

    assert [(f["label"], f["without"]) for f in context["way_out"]] == [("Beginner", 1)]
    after = logged_in.get(context["way_out"][0]["remove_url"], **HTMX).context
    assert after["results_count"] == 1


@pytest.mark.django_db
def test_no_way_out_when_no_single_filter_helps(logged_in, library_url, zorro):
    response = logged_in.get(library_url, {"q": "xyzzy", "muscle": "biceps"}, **HTMX)

    assert response.context["way_out"] == []
    content = response.content.decode()
    assert "Without “" not in content
    assert "picker-way-out" not in content
    assert content.count("Clear filters") == 1  # in the bar
    assert "Add my own exercise: «xyzzy»" in content  # "+ Add…" unchanged

    plain = logged_in.get(library_url, {"q": "xyzzy"}, **HTMX).content.decode()
    assert "picker-way-out" not in plain and "Clear filters" not in plain


@pytest.mark.django_db
def test_way_out_in_polish(client, user, library_url, zorro):
    client.force_login(user)
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "pl"
    params = {"q": "zorro", "muscle": "biceps", "equipment": "smith", "category": WARMUP}

    content = client.get(library_url, params, **HTMX).content.decode()

    assert "Bez filtra «Suwnica Smitha»: 1 ćwiczenie" in content
    assert "Wyczyść filtry" in content


# --- "More filters" ------------------------------------------------------------------


@pytest.mark.django_db
def test_type_and_level_are_folded_by_default(logged_in, library_url, zorro):
    content = logged_in.get(library_url, {"q": "zorro"}).content.decode()

    assert (
        '<input type="checkbox" id="more-filters" name="more" value="1" class="more-filters-input">'
        in content
    )
    assert "More filters" in content
    # The rows are there (CSS hides them), so opening needs no request.
    assert 'name="level" value="beginner"' in content


@pytest.mark.parametrize("params", [{"level": "beginner"}, {"category": "strength"}, {"more": "1"}])
@pytest.mark.django_db
def test_more_filters_open(logged_in, library_url, zorro, params):
    response = logged_in.get(library_url, {"q": "zorro", **params}, **HTMX)

    assert response.context["more_open"]
    assert 'class="more-filters-input" checked' in response.content.decode()


@pytest.mark.django_db
def test_more_filters_stay_open_after_taking_a_filter_off(logged_in, library_url, zorro):
    context = logged_in.get(library_url, {"q": "zorro", "level": "beginner"}, **HTMX).context

    remove = context["chosen_filters"][0]["remove_url"]

    assert _params(remove) == {"q": "zorro", "more": "1"}
    assert logged_in.get(remove, **HTMX).context["more_open"]


# --- the same picker in plans and workouts -------------------------------------------


@pytest.mark.django_db
def test_plan_picker_keeps_its_own_parameters(logged_in, user, zorro):
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="P"), name="A", order=1)
    url = reverse("plans:pe_create", args=[day.pk])

    response = logged_in.get(
        url, {"q": "zorro", "muscle": "chest", "equipment": "dumbbell"}, **HTMX
    )

    assert response.context["results_count"] == 0
    assert [f["label"] for f in response.context["way_out"]] == ["Chest", "Dumbbell"]
    assert _values(response.context, "muscle") == ["chest", "biceps"]


@pytest.mark.django_db
def test_workout_picker_has_the_chips(logged_in, user, make_workout, zorro):
    workout = make_workout(user, days_ago=0, finished=False)
    url = reverse("workouts:add_exercise", args=[workout.pk])

    content = logged_in.get(url, {"q": "zorro", "equipment": "smith"}).content.decode()

    assert "filter-bar" in content and 'id="picker-filters"' in content


@pytest.mark.django_db
def test_extra_parameters_stay_in_the_filter_links(rf, user, zorro):
    """The plan's "Change exercise" picker passes pick=1; taking a filter off keeps it."""
    request = rf.get("/plans/days/1/exercises/new/", {"q": "zorro", "muscle": "biceps"})
    request.user = user

    response = picker_response(
        request, select_base="?exercise=", title="T", back_url="/", extra_params={"pick": "1"}
    )

    content = response.content.decode()
    bar = content.split('class="filter-bar"', 1)[1].split("</div>", 1)[0]
    assert "pick=1" in bar and "q=zorro" in bar


# --- cost ----------------------------------------------------------------------------


@pytest.mark.django_db
def test_counting_adds_at_most_one_query_per_refresh(
    logged_in, library_url, zorro, django_assert_max_num_queries
):
    call_command("seed_exercises")
    params = {"q": "curl", "muscle": "biceps", "equipment": "dumbbell"}
    logged_in.get(library_url, params, **HTMX)

    # Before (2026-11-15): 9 for this request (session, user, language, recent, count, two
    # for the "Type" chips, results, find_by_name). Now the count and the type chips come
    # from the four GROUP BY queries: 10.
    with django_assert_max_num_queries(10):
        logged_in.get(library_url, params, **HTMX)
