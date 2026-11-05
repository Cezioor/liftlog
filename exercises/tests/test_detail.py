import pytest
from django.urls import reverse

from exercises.models import Exercise
from exercises.services import muscles_for_map, search_exercises
from plans.models import Plan, PlanDay


@pytest.fixture
def squat(db):
    return Exercise.objects.create(
        name="Back Squat",
        aliases="przysiad ze sztangą",
        muscle_group="quads",
        equipment="barbell",
        source_id="Barbell_Squat",
        level="beginner",
        primary_muscles=["quadriceps"],
        secondary_muscles=["glutes", "lower back"],
        instructions=["Set the bar on your back.", "Squat down."],
        images=["Barbell_Squat/0.jpg", "Barbell_Squat/1.jpg"],
    )


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


# --- muscles_for_map ------------------------------------------------------


@pytest.mark.django_db
def test_map_uses_imported_muscles(squat):
    assert muscles_for_map(squat) == (["quadriceps"], ["glutes", "lower back"])


@pytest.mark.django_db
def test_map_falls_back_to_muscle_group_for_own_exercises(user):
    mine = Exercise.objects.create(
        name="My Row", muscle_group="back", equipment="cable", owner=user
    )

    assert muscles_for_map(mine) == (["lats", "middle back"], [])


@pytest.mark.django_db
def test_map_ignores_unknown_and_duplicate_muscles(user):
    mine = Exercise.objects.create(
        name="Odd",
        muscle_group="chest",
        equipment="other",
        owner=user,
        primary_muscles=["chest", "wings"],
        secondary_muscles=["chest", "triceps"],
    )

    assert muscles_for_map(mine) == (["chest"], ["triceps"])


# --- detail page ----------------------------------------------------------


@pytest.mark.django_db
def test_detail_page_shows_photos_map_and_instructions(logged_in, squat):
    response = logged_in.get(reverse("exercises:exercise_detail", args=[squat.pk]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "przysiad ze sztangą" in content
    assert 'loading="lazy"' in content
    assert "cdn.jsdelivr.net/gh/yuhonas/free-exercise-db@" in content
    assert "Barbell_Squat/1.jpg" in content
    assert "Set the bar on your back." in content
    assert "Beginner" in content
    # Muscle map: quadriceps strong, glutes and lower back lighter.
    assert 'class="m m-primary"' in content
    assert 'class="m m-secondary"' in content
    assert "Main: Quadriceps" in content
    assert "Helping: Glutes, Lower back" in content
    assert reverse("plans:add_to_plan", args=[squat.pk]) in content


@pytest.mark.django_db
def test_detail_page_shows_my_last_sets(logged_in, user, squat, make_workout):
    make_workout(user, {squat: [(100, 5), (102.5, 4)]})

    content = logged_in.get(reverse("exercises:exercise_detail", args=[squat.pk])).content.decode()

    assert "100 kg × 5" in content
    assert "102.5 kg × 4" in content


@pytest.mark.django_db
def test_detail_page_for_own_exercise_without_photos(logged_in, user):
    mine = Exercise.objects.create(
        name="My Row", muscle_group="back", equipment="cable", owner=user
    )

    content = logged_in.get(reverse("exercises:exercise_detail", args=[mine.pk])).content.decode()

    assert "<img" not in content
    assert "Main: Lats, Middle back" in content
    assert reverse("exercises:exercise_update", args=[mine.pk]) in content


@pytest.mark.django_db
def test_detail_page_hides_other_users_exercises(logged_in, other_user):
    theirs = Exercise.objects.create(
        name="Their Row", muscle_group="back", equipment="cable", owner=other_user
    )

    response = logged_in.get(reverse("exercises:exercise_detail", args=[theirs.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_add_to_plan_lists_my_plan_days(logged_in, user, other_user, squat):
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="PPL"), name="Legs")
    PlanDay.objects.create(plan=Plan.objects.create(owner=other_user, name="Secret"), name="X")

    content = logged_in.get(reverse("plans:add_to_plan", args=[squat.pk])).content.decode()

    assert f"{reverse('plans:pe_create', args=[day.pk])}?exercise={squat.pk}" in content
    assert "Secret" not in content


# --- library list with thumbnails and level filter ------------------------


@pytest.mark.django_db
def test_library_shows_thumbnails_and_links_to_details(logged_in, squat):
    content = logged_in.get(reverse("exercises:exercise_list")).content.decode()

    assert f'href="/exercises/{squat.pk}/"' in content
    assert 'class="thumb"' in content and "Barbell_Squat/0.jpg" in content
    assert 'name="level"' in content


@pytest.mark.django_db
def test_level_filter(user, squat):
    Exercise.objects.create(
        name="Snatch", muscle_group="full_body", equipment="barbell", level="expert"
    )

    assert [e.name for e in search_exercises(user, level="beginner")] == ["Back Squat"]
    assert [e.name for e in search_exercises(user, level="expert")] == ["Snatch"]


@pytest.mark.django_db
def test_exercises_with_polish_names_come_first(user, squat):
    Exercise.objects.create(name="Air Bike", muscle_group="other", equipment="other")

    assert [e.name for e in search_exercises(user)] == ["Back Squat", "Air Bike"]


@pytest.mark.django_db
def test_quick_add_from_library_goes_to_detail_page(logged_in):
    response = logged_in.post(
        reverse("exercises:exercise_quick_add"),
        {"name": "Landmine Press", "next": "/exercises/", "suffix": "/"},
    )

    exercise = Exercise.objects.get(name="Landmine Press")
    assert response.url == f"/exercises/{exercise.pk}/"


@pytest.mark.django_db
def test_own_exercise_muscles_can_be_chosen(logged_in, user):
    logged_in.post(
        reverse("exercises:exercise_create"),
        {
            "name": "Landmine Press",
            "muscle_group": "shoulders",
            "equipment": "barbell",
            "primary_muscles": ["shoulders"],
            "secondary_muscles": ["triceps", "chest"],
        },
    )

    exercise = Exercise.objects.get(name="Landmine Press")
    assert muscles_for_map(exercise) == (["shoulders"], ["triceps", "chest"])
