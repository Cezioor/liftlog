import pytest
from django.urls import reverse

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise


@pytest.fixture
def plan(user):
    return Plan.objects.create(owner=user, name="PPL", is_active=True)


@pytest.fixture
def day(plan):
    return PlanDay.objects.create(plan=plan, name="Push", order=1)


@pytest.fixture
def item(day, bench):
    return PlanExercise.objects.create(day=day, exercise=bench, order=1)


def _pe_create_url(day, exercise):
    return f"{reverse('plans:pe_create', args=[day.pk])}?exercise={exercise.pk}"


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


# --- creating and editing -------------------------------------------------


@pytest.mark.django_db
def test_create_plan_sets_owner_and_first_plan_is_active(logged_in, user):
    response = logged_in.post(reverse("plans:plan_create"), {"name": "Upper/Lower"})

    plan = Plan.objects.get(name="Upper/Lower")
    assert response.url == reverse("plans:plan_detail", args=[plan.pk])
    assert plan.owner == user
    assert plan.is_active


@pytest.mark.django_db
def test_second_plan_is_not_active(logged_in, plan):
    logged_in.post(reverse("plans:plan_create"), {"name": "Another"})

    assert Plan.objects.get(name="Another").is_active is False


@pytest.mark.django_db
def test_activate_deactivates_previous_plan(logged_in, user, plan):
    other = Plan.objects.create(owner=user, name="Full body")

    logged_in.post(reverse("plans:plan_activate", args=[other.pk]))

    plan.refresh_from_db()
    other.refresh_from_db()
    assert other.is_active and not plan.is_active


@pytest.mark.django_db
def test_add_days_in_order(logged_in, plan):
    for name in ["Push", "Pull", "Legs"]:
        logged_in.post(reverse("plans:day_create", args=[plan.pk]), {"name": name})

    assert list(plan.days.values_list("name", "order")) == [
        ("Push", 1),
        ("Pull", 2),
        ("Legs", 3),
    ]


@pytest.mark.django_db
def test_add_exercise_to_day(logged_in, day, bench):
    response = logged_in.post(
        _pe_create_url(day, bench),
        {
            "target_sets": 4,
            "rep_min": 6,
            "rep_max": 10,
            "rest_seconds": 120,
        },
    )

    assert response.status_code == 302
    item = day.exercises.get()
    assert (item.exercise, item.target_sets, item.rep_range, item.rest_seconds) == (
        bench,
        4,
        "6–10",
        120,
    )


@pytest.mark.django_db
def test_rep_min_above_rep_max_is_rejected(logged_in, day, bench):
    response = logged_in.post(
        _pe_create_url(day, bench),
        {"target_sets": 3, "rep_min": 12, "rep_max": 8, "rest_seconds": 90},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["rep_max"]
    assert not day.exercises.exists()


@pytest.mark.django_db
def test_move_exercise_down_swaps_order(logged_in, day, item, squat):
    second = PlanExercise.objects.create(day=day, exercise=squat, order=2)

    logged_in.post(reverse("plans:pe_move", args=[item.pk, "down"]))

    assert list(day.exercises.all()) == [second, item]


@pytest.mark.django_db
def test_move_rejects_unknown_direction(logged_in, item):
    response = logged_in.post(reverse("plans:pe_move", args=[item.pk, "sideways"]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_plan_detail_renders_days_and_exercises(logged_in, plan, item):
    response = logged_in.get(reverse("plans:plan_detail", args=[plan.pk]))

    content = response.content.decode()
    assert "Push" in content
    assert "Bench Press" in content
    assert "3 × 8–12" in content


@pytest.mark.django_db
def test_delete_plan(logged_in, plan, item):
    logged_in.post(reverse("plans:plan_delete", args=[plan.pk]))

    assert not Plan.objects.exists()
    assert not PlanExercise.objects.exists()


# --- other users' data ----------------------------------------------------


@pytest.mark.django_db
def test_plan_list_shows_only_own_plans(client, other_user, plan):
    Plan.objects.create(owner=other_user, name="Secret plan")
    client.force_login(other_user)

    response = client.get(reverse("plans:plan_list"))

    assert [p.name for p in response.context["plans"]] == ["Secret plan"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "method, url_name, arg",
    [
        ("get", "plans:plan_detail", "plan"),
        ("post", "plans:plan_activate", "plan"),
        ("post", "plans:plan_delete", "plan"),
        ("post", "plans:day_create", "plan"),
        ("get", "plans:day_update", "day"),
        ("post", "plans:day_delete", "day"),
        ("get", "plans:pe_create", "day"),
        ("get", "plans:pe_update", "item"),
        ("post", "plans:pe_delete", "item"),
    ],
)
def test_other_users_cannot_touch_my_plan(
    client, other_user, plan, day, item, method, url_name, arg
):
    target = {"plan": plan, "day": day, "item": item}[arg]
    client.force_login(other_user)

    response = getattr(client, method)(reverse(url_name, args=[target.pk]), {"name": "x"})

    assert response.status_code == 404
    assert Plan.objects.filter(pk=plan.pk, name="PPL").exists()
    assert PlanExercise.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_cannot_add_another_users_exercise_to_plan(logged_in, day, other_user):
    private = Exercise.objects.create(
        name="Their move", muscle_group="core", equipment="other", owner=other_user
    )

    response = logged_in.post(
        _pe_create_url(day, private),
        {"target_sets": 3, "rep_min": 8, "rep_max": 12, "rest_seconds": 90},
    )

    assert response.status_code == 404
    assert not day.exercises.exists()


# --- picking the exercise -------------------------------------------------


@pytest.mark.django_db
def test_add_exercise_starts_with_the_picker(logged_in, day, bench):
    response = logged_in.get(reverse("plans:pe_create", args=[day.pk]))

    assert response.templates[0].name == "exercises/picker.html"
    content = response.content.decode()
    # Each result links to the next step with the exercise id.
    assert f'href="{_pe_create_url(day, bench)}"' in content


@pytest.mark.django_db
def test_picked_exercise_shows_sets_form(logged_in, day, bench):
    response = logged_in.get(_pe_create_url(day, bench))

    assert response.templates[0].name == "plans/plan_exercise_form.html"
    assert "Bench Press" in response.content.decode()


@pytest.mark.django_db
def test_change_exercise_of_plan_item(logged_in, item, squat):
    url = reverse("plans:pe_update", args=[item.pk])

    picker = logged_in.get(url, {"pick": "1"}).content.decode()
    # The result links go to the form (without pick=1), not back to the picker.
    assert f'href="{url}?exercise={squat.pk}"' in picker
    logged_in.post(
        f"{url}?exercise={squat.pk}",
        {"target_sets": 3, "rep_min": 8, "rep_max": 12, "rest_seconds": 90},
    )

    item.refresh_from_db()
    assert item.exercise == squat


@pytest.mark.django_db
def test_invalid_exercise_id_is_404(logged_in, day):
    assert (
        logged_in.get(reverse("plans:pe_create", args=[day.pk]), {"exercise": "x"}).status_code
        == 404
    )
