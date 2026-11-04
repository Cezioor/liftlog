"""Business logic for the exercise library."""

from decimal import Decimal

from django.db.models import Case, IntegerField, Value, When

from .models import Equipment, Exercise, MuscleGroup
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


def search_exercises(user, query="", muscle_group="", equipment=""):
    """Exercises visible to `user` matching the query and filters.

    Case and Polish diacritics are ignored ("zgiecia" finds "zgięcia"), and every
    word of the query must appear somewhere in the name or the other names.
    Exercises whose name starts with the query come first.
    """
    results = Exercise.objects.visible_to(user)
    if muscle_group in MuscleGroup.values:
        results = results.filter(muscle_group=muscle_group)
    if equipment in Equipment.values:
        results = results.filter(equipment=equipment)

    normalized = normalize(query)
    for word in normalized.split():
        results = results.filter(search_text__contains=word)
    if normalized:
        results = results.annotate(
            name_first=Case(
                When(search_text__startswith=normalized, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("name_first", "name")
    return results


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
