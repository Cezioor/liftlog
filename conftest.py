"""Shared pytest fixtures for all apps."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from exercises.models import Exercise
from workouts.models import Workout, WorkoutSet


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="ania", password="pass")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="bartek", password="pass")


@pytest.fixture
def bench(db):
    return Exercise.objects.create(name="Bench Press", muscle_group="chest", equipment="barbell")


@pytest.fixture
def squat(db):
    return Exercise.objects.create(name="Back Squat", muscle_group="quads", equipment="barbell")


@pytest.fixture
def pull_up(db):
    return Exercise.objects.create(
        name="Pull-up", muscle_group="back", equipment="bodyweight", is_bodyweight=True
    )


@pytest.fixture
def make_workout(db):
    """make_workout(user, {exercise: [(kg, reps), ...]}, days_ago=1, finished=True)."""

    def factory(owner, sets_by_exercise=None, days_ago=1, finished=True, plan_day=None):
        started = timezone.now() - timedelta(days=days_ago)
        workout = Workout.objects.create(
            owner=owner,
            plan_day=plan_day,
            started_at=started,
            finished_at=started + timedelta(hours=1) if finished else None,
        )
        for exercise, sets in (sets_by_exercise or {}).items():
            for number, (weight, reps, *warmup) in enumerate(sets, start=1):
                WorkoutSet.objects.create(
                    workout=workout,
                    exercise=exercise,
                    order=number,
                    weight_kg=Decimal(str(weight)),
                    reps=reps,
                    is_warmup=bool(warmup and warmup[0]),
                )
        return workout

    return factory
