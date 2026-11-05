"""Data migration: before Stage 1.6 a plank had to be logged as "0 × 60", where 60 meant seconds.

Sets of exercises that are now `time` exercises, logged with no weight and a number in
`reps`, get that number moved into `duration_seconds`. Nothing else is touched:
a time exercise logged with weight ("10 × 60") is listed but left as it is, because
it's not clear what it meant.

The logic stays in this file (not in services.py) because a migration must only use
the historical models it is given, so it keeps working after the models change.
"""

from django.db import migrations
from django.db.models import Q

# Exercise types are filled in by seed_exercises / import_free_exercise_db, which build.sh runs
# *after* migrate. On a database that never had them run, the built-in Plank would still
# look like a weight × reps exercise, so it is named here (it is the only original exercise
# that became a time exercise in Stage 1.6).
BUILT_IN_TIME_EXERCISES = ["Plank"]


def _describe(workout_set):
    return (
        f"set {workout_set.pk} · {workout_set.exercise.name} · "
        f"{workout_set.workout.started_at:%Y-%m-%d} · set {workout_set.order}"
    )


def convert_old_time_sets(apps, schema_editor=None, report=print):
    WorkoutSet = apps.get_model("workouts", "WorkoutSet")
    is_time_exercise = Q(exercise__measurement="time") | Q(
        exercise__owner__isnull=True, exercise__name__in=BUILT_IN_TIME_EXERCISES
    )
    old_style = WorkoutSet.objects.filter(
        is_time_exercise,
        reps__isnull=False,
        duration_seconds__isnull=True,
        distance_m__isnull=True,
    ).select_related("exercise", "workout")

    converted = []
    for workout_set in old_style.order_by("pk"):
        if workout_set.weight_kg:
            report(
                f"  left unchanged (has weight): {_describe(workout_set)}: "
                f"{workout_set.weight_kg.normalize():f} × {workout_set.reps}"
            )
            continue
        report(f"  {_describe(workout_set)}: 0 × {workout_set.reps} -> {workout_set.reps} s")
        workout_set.duration_seconds = workout_set.reps
        workout_set.reps = None
        workout_set.save(update_fields=["duration_seconds", "reps"])
        converted.append(workout_set.pk)

    report(f"  old time sets converted to seconds: {len(converted)}")
    return converted


class Migration(migrations.Migration):
    dependencies = [
        ("workouts", "0003_stage_1_6_types"),
        ("exercises", "0006_exercise_types"),
    ]

    operations = [
        # No way back: after the change a converted set looks like any set timed in seconds.
        migrations.RunPython(convert_old_time_sets, migrations.RunPython.noop),
    ]
