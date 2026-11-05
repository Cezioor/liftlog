"""Business logic for the exercise library."""

from decimal import Decimal

from django.db.models import Case, IntegerField, Q, Value, When

from .models import Equipment, Exercise, Level, Muscle, MuscleGroup
from .text import normalize

LOWER_BODY_GROUPS = {
    MuscleGroup.QUADS,
    MuscleGroup.HAMSTRINGS,
    MuscleGroup.GLUTES,
    MuscleGroup.CALVES,
}

DUMBBELL_STEP = Decimal("2")
LOWER_BODY_STEP = Decimal("5")
UPPER_BODY_STEP = Decimal("2.5")


def default_progression_step(muscle_group, equipment):
    """How many kg the progression hint adds when every set hit the top of the range.

    Equipment wins over muscle group: dumbbells usually go up in 2 kg steps,
    whatever they are used for. Otherwise lower body 5 kg, upper body 2.5 kg.
    """
    if equipment == Equipment.DUMBBELL:
        return DUMBBELL_STEP
    if muscle_group in LOWER_BODY_GROUPS:
        return LOWER_BODY_STEP
    return UPPER_BODY_STEP


def search_exercises(user, query="", muscle_group="", equipment="", level=""):
    """Exercises visible to `user` matching the query and filters.

    Case and Polish diacritics are ignored ("zgiecia" finds "zgięcia"), and every
    word of the query must appear somewhere in the name or the other names.
    Order: name starts with the query, then exercises with Polish names (the common
    ones and the user's own), then alphabetical.
    """
    results = Exercise.objects.visible_to(user)
    if muscle_group in MuscleGroup.values:
        results = results.filter(muscle_group=muscle_group)
    if equipment in Equipment.values:
        results = results.filter(equipment=equipment)
    if level in Level.values:
        results = results.filter(level=level)

    normalized = normalize(query)
    for word in normalized.split():
        results = results.filter(search_text__contains=word)

    ordering = []
    if normalized:
        results = results.annotate(
            name_first=Case(
                When(search_text__startswith=normalized, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        ordering.append("name_first")
    results = results.annotate(
        familiar_first=Case(
            When(Q(owner__isnull=False) | ~Q(aliases=""), then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    )
    return results.order_by(*ordering, "familiar_first", "name")


# Muscles shown on the map for exercises without their own list (user exercises,
# unmatched originals), derived from the muscle group.
GROUP_MUSCLES = {
    MuscleGroup.CHEST: [Muscle.CHEST],
    MuscleGroup.BACK: [Muscle.LATS, Muscle.MIDDLE_BACK],
    MuscleGroup.SHOULDERS: [Muscle.SHOULDERS],
    MuscleGroup.BICEPS: [Muscle.BICEPS],
    MuscleGroup.TRICEPS: [Muscle.TRICEPS],
    MuscleGroup.FOREARMS: [Muscle.FOREARMS],
    MuscleGroup.QUADS: [Muscle.QUADRICEPS],
    MuscleGroup.HAMSTRINGS: [Muscle.HAMSTRINGS],
    MuscleGroup.GLUTES: [Muscle.GLUTES],
    MuscleGroup.CALVES: [Muscle.CALVES],
    MuscleGroup.CORE: [Muscle.ABDOMINALS],
    MuscleGroup.FULL_BODY: [
        Muscle.QUADRICEPS,
        Muscle.GLUTES,
        Muscle.HAMSTRINGS,
        Muscle.LOWER_BACK,
        Muscle.SHOULDERS,
    ],
}


def muscles_for_map(exercise):
    """(primary, secondary) muscle lists for the muscle map; works for every exercise."""
    primary = [m for m in exercise.primary_muscles if m in Muscle.values]
    if not primary:
        primary = [str(m) for m in GROUP_MUSCLES.get(exercise.muscle_group, [])]
    secondary = [m for m in exercise.secondary_muscles if m in Muscle.values and m not in primary]
    return primary, secondary


def find_by_name(user, name, exclude_pk=None):
    """An exercise visible to `user` with the same name, ignoring case and diacritics.

    Compared in Python on normalised names, because SQLite's case-insensitive
    matching only knows ASCII letters ("Ł" != "ł" there).
    """
    wanted = normalize(name)
    if not wanted:
        return None
    candidates = Exercise.objects.visible_to(user).filter(search_text__startswith=wanted)
    if exclude_pk is not None:
        candidates = candidates.exclude(pk=exclude_pk)
    return next((e for e in candidates if normalize(e.name) == wanted), None)
