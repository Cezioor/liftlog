"""Business logic for the exercise library."""

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Case, IntegerField, Q, TextField, Value, When
from django.db.models.functions import Replace

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


# Words in a search that name equipment, after normalize() (no diacritics, lowercase).
# "przysiad hantle" = squats done with dumbbells. English plurals are handled by stem().
EQUIPMENT_WORDS = {
    Equipment.SMITH: {"smith", "smitha", "suwnica", "suwnicy", "suwnice", "suwnicach"},
    Equipment.DUMBBELL: {"hantle", "hantla", "hantli", "hantlami", "hantlem", "hantel",
                         "hantelki", "dumbbell", "db"},
    Equipment.BARBELL: {"sztanga", "sztangi", "sztange", "sztangach", "barbell",
                        "gryf", "gryfem"},
    Equipment.KETTLEBELL: {"kettlebell", "kettla", "kettle", "kettlem", "kb", "odwaznik"},
    Equipment.CABLE: {"wyciag", "wyciagu", "wyciagiem", "wyciagach", "linka", "linki", "linke",
                      "cable"},
    Equipment.BAND: {"gumy", "guma", "gume", "gumie", "gumami", "band", "tasma", "tasmy"},
    Equipment.MACHINE: {"maszyna", "maszynie", "maszyne", "maszyny", "machine"},
}  # fmt: skip
WORD_TO_EQUIPMENT = {
    word: equipment for equipment, words in EQUIPMENT_WORDS.items() for word in words
}


def stem(word):
    """Crude English singular, enough for exercise names: "ups" -> "up",
    "presses" -> "press", "crunches" -> "crunch", "flies" -> "fly".

    Only the query is stemmed; it is then searched as a substring, so "lunge" still
    matches "Lunges" in the library.
    """
    if word.endswith("sses") or word.endswith(("ches", "shes", "xes")):
        return word[:-2]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith(("ss", "us")) and len(word) >= 3:
        return word[:-1]
    return word


@dataclass(frozen=True)
class ParsedQuery:
    words: list  # stemmed words without spaces between them mattering
    equipment: str = ""  # equipment named in the query, e.g. "smith"
    equipment_word: str = ""  # the word that named it, e.g. "suwnica"


def parse_query(query):
    """Split a search into movement words and an equipment word.

    "step up smith machine" -> words ["step", "up"], equipment smith ("machine" is
    part of "Smith machine", not a second piece of equipment).
    """
    words, equipment, equipment_word = [], "", ""
    for word in normalize(query).split():
        named = WORD_TO_EQUIPMENT.get(word) or WORD_TO_EQUIPMENT.get(stem(word))
        if named and not equipment:
            equipment, equipment_word = named, word
        elif named:
            continue  # a second equipment word: "smith machine", "hantle dumbbell"
        else:
            words.append(stem(word))
    return ParsedQuery(words, equipment, equipment_word)


def _compact(text):
    return text.replace(" ", "")


def search_exercises(user, query="", muscle_group="", equipment="", level=""):
    """Exercises visible to `user` matching the query and filters.

    - Case, Polish diacritics, hyphens and spaces don't matter, nor English plurals:
      "step up" = "step-up" = "stepup" = "step ups".
    - Every word must appear somewhere in the name or the other names.
    - A word naming equipment ("smith", "hantle", "wyciąg"…) matches exercises with that
      equipment, or with that word in a name ("suwnica" also finds the leg press).
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

    parsed = parse_query(query)
    # The names without spaces, so "stepup" finds "step up" and the other way round.
    results = results.annotate(
        compact=Replace("search_text", Value(" "), Value(""), output_field=TextField())
    )
    for word in parsed.words:
        results = results.filter(compact__contains=word)
    if parsed.equipment:
        # Any form of the word counts in a name ("suwnica" finds "…na suwnicy"); short
        # ones like "db" are left out, they'd match inside other words.
        in_name = Q()
        for word in EQUIPMENT_WORDS[parsed.equipment]:
            if len(word) >= 4:
                in_name |= Q(compact__contains=word)
        results = results.filter(Q(equipment=parsed.equipment) | in_name)

    ordering = []
    start = "".join(parsed.words)
    if start:
        results = results.annotate(
            name_first=Case(
                When(compact__startswith=start, then=Value(0)),
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


# --- variants -----------------------------------------------------------------


# Words that only say which equipment an exercise uses ("Barbell Step Ups").
NAME_EQUIPMENT_WORDS = {
    word for words in EQUIPMENT_WORDS.values() for word in words if len(word) >= 4
} | {"ez", "bar", "smith", "machine", "cable", "cables", "kettlebells", "dumbbells"}


def movement_name(name):
    """The exercise name without equipment words: "Barbell Step Ups" -> "Step Ups",
    "Smith Machine Squat" -> "Squat". Unchanged if nothing would be left."""
    kept = [w for w in name.split() if normalize(w) not in NAME_EQUIPMENT_WORDS]
    return " ".join(kept) or name


def _extra_words(exercise, query_words):
    """How many words of the exercise's movement name the query didn't ask for.
    "Step Ups" for "step up" -> 0, "Step-up with Knee Raise" -> 3."""
    words = normalize(movement_name(exercise.name)).split()
    return sum(1 for w in words if not any(q in w or stem(w) in q for q in query_words))


@dataclass(frozen=True)
class VariantSuggestion:
    base: Exercise
    equipment: str

    @property
    def equipment_label(self):
        return Equipment(self.equipment).label

    @property
    def movement(self):
        return movement_name(self.base.name)


def variant_suggestion(user, query):
    """ "Add variant: «Step Ups» — Smith machine" when the query names a movement and a
    piece of equipment, the movement exists, but not with that equipment.

    The base is the plainest match: the fewest words beyond what was typed
    ("Barbell Step Ups" over "Step-up with Knee Raise"). If that is itself a variant,
    its own base is used (variants of variants would only confuse).
    """
    parsed = parse_query(query)
    if not parsed.equipment or not parsed.words:
        return None
    movement = search_exercises(user, " ".join(parsed.words))
    if movement.filter(equipment=parsed.equipment).exists():
        return None
    candidates = list(movement[:20])
    if not candidates:
        return None
    base = min(candidates, key=lambda e: _extra_words(e, parsed.words))  # stable: keeps order
    return VariantSuggestion(base.variant_of or base, parsed.equipment)


def variant_name(base, equipment):
    """ "Barbell Step Ups" + Smith machine -> "Step Ups (Smith machine)"."""
    return f"{movement_name(base.name)} ({Equipment(equipment).label})"[:100]


def create_variant(user, base, equipment):
    """The user's own copy of `base` with other equipment.

    Muscles, measurement type, category, instructions and photos come from the base;
    equipment (and so the default weight step) is the new one. History and records
    are separate because it is a separate exercise. Returns the existing variant if
    the user already has one with that name.
    """
    name = variant_name(base, equipment)
    existing = find_by_name(user, name)
    if existing is not None:
        return existing
    return Exercise.objects.create(
        owner=user,
        name=name,
        variant_of=base,
        aliases=base.aliases,
        muscle_group=base.muscle_group,
        equipment=equipment,
        is_bodyweight=equipment == Equipment.BODYWEIGHT,
        measurement=base.measurement,
        category=base.category,
        is_unilateral=base.is_unilateral,
        primary_muscles=list(base.primary_muscles),
        secondary_muscles=list(base.secondary_muscles),
        level=base.level,
        mechanic=base.mechanic,
        instructions=list(base.instructions),
        images=list(base.images),
        progression_step_kg=default_progression_step(base.muscle_group, equipment),
    )


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
