"""The exercise picker, tested through the workout's "Add exercise" screen."""

import pytest
from django.core.management import call_command
from django.urls import reverse

from exercises.models import Exercise

HTMX_RESULTS = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "picker-results"}


@pytest.fixture
def workout(user, make_workout):
    return make_workout(user, days_ago=0, finished=False)


@pytest.fixture
def picker_url(workout):
    return reverse("workouts:add_exercise", args=[workout.pk])


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def library(db):
    call_command("seed_exercises")


@pytest.mark.django_db
def test_full_page_on_first_visit(logged_in, picker_url, library):
    response = logged_in.get(picker_url)

    assert response.templates[0].name == "exercises/picker.html"
    content = response.content.decode()
    assert 'type="search"' in content
    assert 'hx-trigger="input changed delay:250ms, search, submit"' in content
    assert "All exercises" in content


@pytest.mark.django_db
def test_htmx_search_returns_only_results(logged_in, picker_url, library):
    response = logged_in.get(picker_url, {"q": "przysiad"}, **HTMX_RESULTS)

    assert response.templates[0].name == "exercises/partials/picker_results.html"
    content = response.content.decode()
    assert "Back Squat" in content
    assert "Bench Press" not in content
    assert "<html" not in content


@pytest.mark.django_db
def test_results_link_to_select_url(logged_in, picker_url, library):
    squat = Exercise.objects.get(name="Back Squat")

    content = logged_in.get(picker_url, {"q": "squat"}, **HTMX_RESULTS).content.decode()

    assert f'href="{picker_url}?exercise={squat.pk}"' in content


@pytest.mark.django_db
def test_filter_chips(logged_in, picker_url, library):
    response = logged_in.get(picker_url, {"muscle": "calves"}, **HTMX_RESULTS)

    names = [e.name for e in response.context["results"]]
    assert names == ["Seated Calf Raise", "Single-Leg Balance", "Standing Calf Raise"]


@pytest.mark.django_db
def test_recently_used_on_top_until_you_search(logged_in, user, picker_url, library, make_workout):
    squat = Exercise.objects.get(name="Back Squat")
    curl = Exercise.objects.get(name="Barbell Curl")
    make_workout(user, {curl: [(30, 10)]}, days_ago=3)
    make_workout(user, {squat: [(100, 5)]}, days_ago=1)

    response = logged_in.get(picker_url)
    assert response.context["recent"] == [squat, curl]
    assert "Recently used" in response.content.decode()

    response = logged_in.get(picker_url, {"q": "curl"}, **HTMX_RESULTS)
    assert response.context["recent"] == []


@pytest.mark.django_db
def test_recently_used_ignores_other_users(
    logged_in, other_user, picker_url, library, make_workout
):
    make_workout(other_user, {Exercise.objects.get(name="Deadlift"): [(200, 1)]})

    assert logged_in.get(picker_url).context["recent"] == []


@pytest.mark.django_db
def test_add_my_own_is_offered_for_new_names_only(logged_in, picker_url, library):
    new = logged_in.get(picker_url, {"q": "Wiosłowanie Meadowsa"}, **HTMX_RESULTS)
    existing = logged_in.get(picker_url, {"q": "back squat"}, **HTMX_RESULTS)

    assert "Add my own: «Wiosłowanie Meadowsa»" in new.content.decode()
    assert "Add my own" not in existing.content.decode()


@pytest.mark.django_db
def test_quick_add_creates_exercise_and_selects_it(logged_in, user, workout, picker_url):
    response = logged_in.post(
        reverse("exercises:exercise_quick_add"),
        {
            "name": "Wiosłowanie Meadowsa",
            "muscle": "back",
            "equipment": "barbell",
            "next": f"{picker_url}?exercise=",
        },
    )

    exercise = Exercise.objects.get(name="Wiosłowanie Meadowsa")
    assert (exercise.owner, exercise.muscle_group, exercise.equipment) == (user, "back", "barbell")
    assert response.url == f"{picker_url}?exercise={exercise.pk}"
    # Following it adds the exercise to the workout.
    final = logged_in.get(response.url)
    assert final.url.endswith(f"?add={exercise.pk}#ex-{exercise.pk}")
    assert "Wiosłowanie Meadowsa" in logged_in.get(final.url).content.decode()


@pytest.mark.django_db
def test_quick_add_without_filters_uses_other(logged_in, picker_url):
    logged_in.post(
        reverse("exercises:exercise_quick_add"),
        {"name": "Mystery move", "next": f"{picker_url}?exercise="},
    )

    exercise = Exercise.objects.get(name="Mystery move")
    assert (exercise.muscle_group, exercise.equipment) == ("other", "other")


@pytest.mark.django_db
def test_quick_add_reuses_existing_exercise(logged_in, picker_url, library):
    squat = Exercise.objects.get(name="Back Squat")

    response = logged_in.post(
        reverse("exercises:exercise_quick_add"),
        {"name": "back SQUAT", "next": f"{picker_url}?exercise="},
    )

    assert response.url.endswith(f"?exercise={squat.pk}")
    assert Exercise.objects.filter(name__iexact="back squat").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "next_url", ["https://evil.example/?x=", "//evil.example/", "javascript:alert(1)//", ""]
)
def test_quick_add_rejects_external_return_address(logged_in, next_url):
    response = logged_in.post(
        reverse("exercises:exercise_quick_add"), {"name": "Something", "next": next_url}
    )

    assert response.status_code == 400
    assert not Exercise.objects.filter(name="Something").exists()


@pytest.mark.django_db
def test_quick_add_requires_login(client):
    response = client.post(reverse("exercises:exercise_quick_add"), {"name": "x", "next": "/"})

    assert response.status_code == 302
    assert not Exercise.objects.exists()


@pytest.mark.django_db
def test_picking_another_users_exercise_is_404(logged_in, picker_url, other_user):
    theirs = Exercise.objects.create(
        name="Their move", muscle_group="core", equipment="other", owner=other_user
    )

    assert logged_in.get(picker_url, {"exercise": theirs.pk}).status_code == 404
    assert logged_in.get(picker_url, {"exercise": "abc"}).status_code == 404


@pytest.mark.django_db
def test_other_user_cannot_open_picker_for_my_workout(client, other_user, picker_url):
    client.force_login(other_user)

    assert client.get(picker_url).status_code == 404
