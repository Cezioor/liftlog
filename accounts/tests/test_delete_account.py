import pytest
from django.db.models import RestrictedError

from exercises.models import Exercise
from plans.models import Plan, PlanDay, PlanExercise
from workouts.models import Workout, WorkoutSet


@pytest.fixture
def own_exercise_in_use(user, make_workout):
    exercise = Exercise.objects.create(
        name="My Row", muscle_group="back", equipment="cable", owner=user
    )
    make_workout(user, {exercise: [(50, 10)]})
    day = PlanDay.objects.create(plan=Plan.objects.create(owner=user, name="P"), name="D")
    PlanExercise.objects.create(day=day, exercise=exercise)
    return exercise


@pytest.mark.django_db
def test_deleting_account_removes_own_exercises_plans_and_workouts(user, own_exercise_in_use):
    user.delete()

    assert not Exercise.objects.filter(pk=own_exercise_in_use.pk).exists()
    assert not Workout.objects.exists()
    assert not WorkoutSet.objects.exists()
    assert not PlanExercise.objects.exists()


@pytest.mark.django_db
def test_exercise_in_use_cannot_be_deleted_on_its_own(own_exercise_in_use):
    with pytest.raises(RestrictedError):
        own_exercise_in_use.delete()
