"""Business logic for the exercise library."""

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Case, F, IntegerField, Q, TextField, Value, When
from django.db.models.functions import Cast, Replace
from django.utils import translation

from .models import Category, Equipment, Exercise, Level, Movement, Muscle, MuscleGroup
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
    Equipment.SMITH: {"smith", "smitha", "smithie", "smithem", "smithu", "suwnica", "suwnicy",
                      "suwnice", "suwnicach"},
    Equipment.DUMBBELL: {"hantle", "hantla", "hantli", "hantlami", "hantlem", "hantlach",
                         "hantel", "hantelki", "dumbbell", "db"},
    Equipment.BARBELL: {"sztanga", "sztangi", "sztange", "sztangach", "sztangami", "barbell",
                        "gryf", "gryfem"},
    Equipment.KETTLEBELL: {"kettlebell", "kettlebella", "kettlebellem", "kettlebellami",
                           "kettla", "kettle", "kettli", "kettlem", "kb", "odwaznik",
                           "odwaznikiem"},
    Equipment.CABLE: {"wyciag", "wyciagu", "wyciagiem", "wyciagach", "linka", "linki", "linke",
                      "cable"},
    Equipment.BAND: {"gumy", "guma", "gume", "gumie", "gumami", "gumach", "band", "tasma",
                     "tasmy"},
    Equipment.MACHINE: {"maszyna", "maszynie", "maszyne", "maszyny", "maszynach", "machine"},
    Equipment.PLATE: {"talerz", "talerza", "talerzem", "talerzu", "talerze", "talerzy",
                      "talerzami", "plate"},
    Equipment.PULLUP_BAR: {"drazek", "drazku", "drazkiem", "drazka", "drazkach"},
    Equipment.LANDMINE: {"landmine", "landmina", "landminie"},
    Equipment.SUSPENSION: {"trx", "suspension"},
    Equipment.BODYWEIGHT: {"bodyweight"},
}  # fmt: skip
WORD_TO_EQUIPMENT = {
    word: equipment for equipment, words in EQUIPMENT_WORDS.items() for word in words
}


@dataclass(frozen=True)
class MuscleTarget:
    """What a muscle word in a search means: these muscle groups, or these muscles
    (Exercise.primary_muscles / secondary_muscles, the muscle map's names)."""

    groups: frozenset
    muscles: frozenset


def _target(groups, muscles):
    return MuscleTarget(frozenset(groups), frozenset(muscles))


LEG_GROUPS = (MuscleGroup.QUADS, MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES, MuscleGroup.CALVES)
LEG_MUSCLES = (Muscle.QUADRICEPS, Muscle.HAMSTRINGS, Muscle.GLUTES, Muscle.CALVES,
               Muscle.ADDUCTORS, Muscle.ABDUCTORS)  # fmt: skip
MUSCLE_TARGETS = {
    "glutes": _target([MuscleGroup.GLUTES], [Muscle.GLUTES]),
    "chest": _target([MuscleGroup.CHEST], [Muscle.CHEST]),
    "back": _target([MuscleGroup.BACK], [Muscle.LATS, Muscle.MIDDLE_BACK, Muscle.LOWER_BACK]),
    "shoulders": _target([MuscleGroup.SHOULDERS], [Muscle.SHOULDERS]),
    "biceps": _target([MuscleGroup.BICEPS], [Muscle.BICEPS]),
    "triceps": _target([MuscleGroup.TRICEPS], [Muscle.TRICEPS]),
    "forearms": _target([MuscleGroup.FOREARMS], [Muscle.FOREARMS]),
    "quads": _target([MuscleGroup.QUADS], [Muscle.QUADRICEPS]),
    "hamstrings": _target([MuscleGroup.HAMSTRINGS], [Muscle.HAMSTRINGS]),
    "calves": _target([MuscleGroup.CALVES], [Muscle.CALVES]),
    "legs": _target(LEG_GROUPS, LEG_MUSCLES),  # "nogi": the whole legs, not only the quads
    "core": _target([MuscleGroup.CORE], [Muscle.ABDOMINALS]),
    "traps": _target([], [Muscle.TRAPS]),  # no muscle group of their own
}
# Words in a search that name a muscle (after normalize()), formal and colloquial, Polish
# and English. Like equipment words they filter instead of having to be in the name.
MUSCLE_WORDS = {
    "glutes": {"posladki", "posladek", "posladka", "posladkow", "posladkach", "posladkami",
               "dupa", "dupe", "dupy", "dupie", "dupka", "dupke", "tylek", "tylka", "tylku",
               "pupa", "pupe", "pupy", "glute", "glutes", "butt"},
    "chest": {"klata", "klate", "klaty", "klacie", "klatka", "klatke", "klatki", "klatce",
              "chest"},
    "back": {"plecy", "plecow", "plecach", "plecami", "grzbiet", "grzbietu", "back", "lats"},
    "shoulders": {"barki", "barkow", "barkach", "bark", "barku", "shoulders", "shoulder",
                  "delts"},
    "biceps": {"biceps", "bicepsa", "bicepsy", "bicepsow", "bicki", "bickow", "bica",
               "bicep"},
    "triceps": {"triceps", "tricepsa", "tricepsy", "tricepsow", "tricki", "trickow", "tricep"},
    "forearms": {"przedramiona", "przedramie", "przedramion", "przedramienia", "forearms",
                 "forearm"},
    "quads": {"uda", "udo", "ud", "udach", "czworki", "czworke", "czworoglowe",
              "czworoglowych", "quads", "quad"},
    "hamstrings": {"dwuglowe", "dwuglowych", "dwojki", "hamstringi", "hamstrings",
                   "hamstring"},
    "calves": {"lydki", "lydka", "lydek", "lydkach", "lydy", "calves", "calf"},
    "legs": {"nogi", "nog", "nogach", "nogami", "noge", "legs"},
    "core": {"brzuch", "brzucha", "brzuchu", "brzuszek", "abs", "absy", "core", "kaloryfer",
             "kaloryfera"},
    "traps": {"kaptury", "kapturow", "kaptur", "trapezy", "traps"},
}  # fmt: skip
WORD_TO_MUSCLE = {word: key for key, words in MUSCLE_WORDS.items() for word in words}
# Two-word names, read before single words ("tył uda" is not the front of the thigh).
PHRASES = {
    "tyl uda": ("muscle", "hamstrings"),
    "tylu uda": ("muscle", "hamstrings"),
    "tyl ud": ("muscle", "hamstrings"),
    "miesnie brzucha": ("muscle", "core"),
    "miesni brzucha": ("muscle", "core"),
    "masa ciala": ("equipment", Equipment.BODYWEIGHT),
    "masy ciala": ("equipment", Equipment.BODYWEIGHT),
    "bez sprzetu": ("equipment", Equipment.BODYWEIGHT),
}
# Words that only fill a sentence: "ćwiczenie na smithie na dupę", "glute exercises smith".
FILLER_WORDS = {
    "cwiczenie", "cwiczenia", "cwiczen", "na", "do", "z", "ze", "dla", "w", "pod", "i",
    "jakies", "jakis", "exercise", "exercises", "for", "with", "on",
}  # fmt: skip


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
    muscle: str = ""  # muscle named in the query: a MUSCLE_TARGETS key, e.g. "glutes"
    # Every word but the fillers, in order ("back squat" -> ["back", "squat"]): a name that
    # starts with them still comes first, even when "back" also names a muscle.
    all_words: tuple = ()


def parse_query(query):
    """Split a search into movement words, an equipment word and a muscle word.

    "step up smith machine" -> words ["step", "up"], equipment smith ("machine" is part
    of "Smith machine", not a second piece of equipment).
    "ćwiczenie na smithie na dupę" -> no words, equipment smith, muscle glutes
    (filler words like "ćwiczenie", "na" are dropped).
    """
    text = f" {normalize(query)} "
    equipment, equipment_word, muscle = "", "", ""
    for phrase, (kind, value) in PHRASES.items():
        if f" {phrase} " in text:
            text = text.replace(f" {phrase} ", " ")
            if kind == "muscle" and not muscle:
                muscle = value
            elif kind == "equipment" and not equipment:
                equipment, equipment_word = value, phrase
    words, all_words = [], []
    for word in text.split():
        if word in FILLER_WORDS:
            continue
        all_words.append(stem(word))
        named = WORD_TO_EQUIPMENT.get(word) or WORD_TO_EQUIPMENT.get(stem(word))
        muscle_named = WORD_TO_MUSCLE.get(word) or WORD_TO_MUSCLE.get(stem(word))
        if named:
            if not equipment:  # a second one: "smith machine", "hantle dumbbell"
                equipment, equipment_word = named, word
        elif muscle_named:
            if not muscle:
                muscle = muscle_named
        else:
            words.append(stem(word))
    return ParsedQuery(words, equipment, equipment_word, muscle, tuple(all_words))


def popular_exercises(user):
    """Q for the exercises suggested first: the 65 common ones LiftLog was seeded with
    (seed_data.EXERCISES) and the ones this user has logged."""
    from workouts.models import WorkoutSet  # workouts imports this app's models

    from .seed_data import EXERCISES

    common = [name for name, *_ in EXERCISES]
    logged = WorkoutSet.objects.filter(workout__owner=user).values("exercise_id")
    return Q(owner__isnull=True, name__in=common) | Q(pk__in=logged)


def _muscles_as_text(field):
    """A muscles JSON list as text ('["glutes", "hamstrings"]'), searchable the same way
    on SQLite and Postgres."""
    return Cast(field, TextField())


def muscle_match(target):
    """Q for exercises whose muscle group or main muscles are `target` (strong match)."""
    query = Q(muscle_group__in=target.groups)
    for muscle in target.muscles:
        query |= Q(primary_text__contains=f'"{muscle}"')
    return query


def helping_muscle_match(target):
    """Q for exercises that work `target` as a helping muscle (weaker match)."""
    query = Q(pk__in=[])
    for muscle in target.muscles:
        query |= Q(secondary_text__contains=f'"{muscle}"')
    return query


def _compact(text):
    return text.replace(" ", "")


def search_exercises(user, query="", muscle_group="", equipment="", level=""):
    """Exercises visible to `user` matching the query and filters.

    - Case, Polish diacritics, hyphens and spaces don't matter, nor English plurals:
      "step up" = "step-up" = "stepup" = "step ups".
    - Every word must appear somewhere in the name or the other names.
    - A word naming equipment ("smith", "hantle", "wyciąg"…) matches exercises with that
      equipment, or with that word in a name ("suwnica" also finds the leg press).
    - A word naming a muscle ("dupa", "klata", "glutes"…) works the same way: exercises
      for that muscle (group, main or helping muscle), or with that word in a name
      ("przyciąganie kolan do klatki" is still found by "klatki").
    - Filler words ("ćwiczenie", "na", "for"…) are ignored.
    Order: name starts with the query, then (with a muscle word) the muscle as group or
    main muscle before the muscle as helping one, then exercises with Polish names (the
    common ones and the user's own), then alphabetical.
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
    if parsed.muscle:
        target = MUSCLE_TARGETS[parsed.muscle]
        results = results.annotate(
            primary_text=_muscles_as_text("primary_muscles"),
            secondary_text=_muscles_as_text("secondary_muscles"),
        )
        # As with equipment: any form of the word in a name counts too ("na plecach").
        in_name = Q(pk__in=[])
        for word in MUSCLE_WORDS[parsed.muscle]:
            if len(word) >= 4:
                in_name |= Q(compact__contains=word)
        strong, helping = muscle_match(target), helping_muscle_match(target)
        results = results.filter(strong | helping | in_name).annotate(
            muscle_rank=Case(
                When(strong, then=Value(0)),
                When(helping, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )

    starts = {"".join(parsed.words), "".join(parsed.all_words)} - {""}
    if starts:
        first = Q()
        for start in starts:
            first |= Q(compact__startswith=start)
        results = results.annotate(
            name_first=Case(
                When(first, then=Value(0)), default=Value(1), output_field=IntegerField()
            )
        )
        ordering.append("name_first")
    if parsed.muscle:
        # Within a muscle: the common exercises and the user's own history first, so
        # "na tyłek" starts with hip thrusts and squats, not with foam rolling.
        results = results.annotate(
            popular_first=Case(
                When(popular_exercises(user), then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        # Stretching and foam rolling after the exercises that train the muscle.
        results = results.annotate(
            stretch_last=Case(
                When(category=Category.MOBILITY, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        ordering += ["muscle_rank", "popular_first", "stretch_last"]
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
# Not "bodyweight": "Bodyweight Squat" is its own movement, and dropping the word would put
# it in the "squat" family with the barbell squat (group_movements would regroup families).
NAME_EQUIPMENT_WORDS = {
    word
    for equipment, words in EQUIPMENT_WORDS.items()
    if equipment != Equipment.BODYWEIGHT
    for word in words
    if len(word) >= 4
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


def family(user, exercise):
    """All variants of the exercise's movement the user can see, itself included."""
    if exercise.movement_id is None:
        return Exercise.objects.filter(pk=exercise.pk)
    return Exercise.objects.visible_to(user).filter(movement_id=exercise.movement_id)


def ensure_movement(exercise):
    """The exercise's family, created on first use (a family of one so far).

    A built-in exercise gets a built-in family, a user's own exercise a family of
    that user, so nobody else ever sees it.
    """
    if exercise.movement_id is None:
        exercise.movement = Movement.objects.create(
            name=movement_name(exercise.name), owner=exercise.owner
        )
        exercise.save(update_fields=["movement"])
    return exercise.movement


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
    ("Barbell Step Ups" over "Step-up with Knee Raise").
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
    if family(user, base).filter(equipment=parsed.equipment).exists():
        return None
    return VariantSuggestion(base, parsed.equipment)


# At most this many "You can also do these on the Smith machine" suggestions.
EQUIPMENT_SUGGESTIONS_LIMIT = 5


# A movement can be done with the key's equipment when its family has a version with one of
# these (free weights that load the body the same way). Machines, pull-up bars, bodyweight,
# TRX and landmine are specific to their movements, so nothing is suggested for them.
SIMILAR_EQUIPMENT = {
    Equipment.SMITH: {Equipment.BARBELL},
    Equipment.BARBELL: {Equipment.DUMBBELL, Equipment.SMITH},
    Equipment.DUMBBELL: {Equipment.BARBELL, Equipment.KETTLEBELL},
    Equipment.KETTLEBELL: {Equipment.DUMBBELL},
    Equipment.CABLE: {Equipment.DUMBBELL, Equipment.BAND},
    Equipment.BAND: {Equipment.CABLE},
}
# Olympic lifts and strongman events are not moved to other equipment.
NOT_MOVED_CATEGORIES = {"olympic weightlifting", "strongman"}


def equipment_fits(user, exercise, equipment):
    """Whether doing `exercise` with `equipment` makes sense.

    The movement needs a version with similar equipment (SIMILAR_EQUIPMENT): for the Smith
    machine a barbell version (a squat yes, a hammer curl no). For anything but the Smith
    machine, at least two built-in exercises with the same muscle group and mechanic
    (compound / isolation) must also use that equipment.
    """
    similar = SIMILAR_EQUIPMENT.get(equipment)
    if (
        not similar
        or exercise.source_category in NOT_MOVED_CATEGORIES
        or exercise.muscle_group == MuscleGroup.FULL_BODY  # e.g. Power Clean ("strength")
    ):
        return False
    versions = {exercise.equipment} | set(
        family(user, exercise).values_list("equipment", flat=True)
    )
    if not versions & similar:
        return False
    if equipment == Equipment.SMITH:
        return True
    same_kind = Exercise.objects.filter(
        owner__isnull=True,
        muscle_group=exercise.muscle_group,
        mechanic=exercise.mechanic,
        equipment=equipment,
    )
    return same_kind.count() >= 2


# Words that don't change the movement: "Back Squat" = "Squat", "Hammer Curl" =
# "Cable Hammer Curls - Rope Attachment". "Incline" or "Close-Grip" do change it.
NOT_DISTINGUISHING_WORDS = {"back", "bench", "seated", "standing", "walking", "rope",
                            "attachment", "with", "the"}  # fmt: skip


def _movement_words(name):
    return {stem(word) for word in normalize(movement_name(name)).split()}


def _similar_name_exists(user, exercise, equipment):
    """An exercise with `equipment` whose movement name differs only by words that don't
    change the movement ("Smith Machine Squat" for "Back Squat"): families don't join all
    of these, and a suggestion would duplicate it."""
    words = _movement_words(exercise.name)
    neutral = {stem(word) for word in NOT_DISTINGUISHING_WORDS}
    for name in (
        Exercise.objects.visible_to(user).filter(equipment=equipment).values_list("name", flat=True)
    ):
        other = _movement_words(name)
        if other and (words ^ other) <= neutral:
            return True
    return False


def equipment_suggestions(user, muscle, equipment, limit=EQUIPMENT_SUGGESTIONS_LIMIT):
    """For "ćwiczenie na smithie na dupę": popular exercises for the muscle that have no
    version with that equipment yet, but where it fits; each can become the user's
    variant in one tap ("+ Add variant"). Only exercises with that muscle as group or
    main muscle (a helping muscle would suggest an Arnold press for triceps); one per
    movement family. Empty when there is nothing to suggest.
    """
    if muscle not in MUSCLE_TARGETS or equipment not in Equipment.values:
        return []
    target = MUSCLE_TARGETS[muscle]
    candidates = (
        Exercise.objects.visible_to(user)
        .filter(popular_exercises(user))
        .exclude(equipment=equipment)
        .annotate(primary_text=_muscles_as_text("primary_muscles"))
        .filter(muscle_match(target))
        .order_by("name")
    )
    suggestions, seen = [], set()
    for exercise in candidates:
        movement = exercise.movement_id or f"exercise-{exercise.pk}"
        if movement in seen:
            continue
        seen.add(movement)
        if family(user, exercise).filter(equipment=equipment).exists():
            continue  # already has a version with it: it is in the results above
        if _similar_name_exists(user, exercise, equipment):
            continue  # e.g. Smith Machine Squat for Back Squat, in another family
        if equipment_fits(user, exercise, equipment):
            suggestions.append(VariantSuggestion(exercise, equipment))
            if len(suggestions) == limit:
                break
    return suggestions


def variant_name(base, equipment, label=""):
    """ "Barbell Step Ups" + Smith machine -> "Step Ups (Smith machine)";
    with "Other…" the typed label: "Step Ups (weighted vest)"."""
    if not label.strip():
        # A saved exercise name: always in English, whatever the page language.
        with translation.override("en"):
            label = str(Equipment(equipment).label)
    return f"{movement_name(base.name)} ({label.strip()})"[:100]


def family_origin(user, exercise):
    """What new variants of `exercise` are made from: the exercise itself if it is
    built-in, otherwise its family's built-in exercise (the oldest one), otherwise the
    user's oldest exercise in the family, the one without an "(equipment)" suffix.

    Without this, a variant of a variant got both suffixes:
    "Hammer Curl (Bodyweight) (Kettlebell)".
    """
    if exercise.is_builtin or exercise.movement_id is None:
        return exercise
    return family(user, exercise).order_by(F("owner").asc(nulls_first=True), "pk").first()


def create_variant(user, base, equipment, label=""):
    """The user's own copy of `base` with other equipment, in the same family.

    Muscles, measurement type, category, instructions and photos come from the base
    (for a user's own variant: from its family's origin, see family_origin); equipment
    (and so the default weight step) is the new one. History and records are separate
    because it is a separate exercise. Returns the existing exercise if the user can
    already see one with that name.
    """
    base = family_origin(user, base)
    name = variant_name(base, equipment, label)
    existing = find_by_name(user, name)
    if existing is not None:
        return existing
    return Exercise.objects.create(
        owner=user,
        name=name,
        movement=ensure_movement(base),
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


# The "Change variant" list of equipment, in this order.
VARIANT_EQUIPMENT = [
    Equipment.SMITH,
    Equipment.DUMBBELL,
    Equipment.BARBELL,
    Equipment.KETTLEBELL,
    Equipment.PLATE,
    Equipment.PULLUP_BAR,
    Equipment.CABLE,
    Equipment.MACHINE,
    Equipment.BAND,
    Equipment.LANDMINE,
    Equipment.SUSPENSION,
    Equipment.BODYWEIGHT,
]


@dataclass(frozen=True)
class VariantChoices:
    current: Exercise
    variants: list  # the family, current first
    equipment: list  # [(value, label)] with no variant yet


def variant_choices(user, exercise):
    """What "Change variant" offers: the existing variants, then equipment without one."""
    variants = sorted(
        family(user, exercise), key=lambda e: (e.pk != exercise.pk, e.owner_id is None, e.name)
    )
    taken = {e.equipment for e in variants}
    equipment = [(e.value, e.label) for e in VARIANT_EQUIPMENT if e not in taken]
    return VariantChoices(exercise, variants, equipment)


class InvalidVariantChoice(ValueError):
    pass


def choose_variant(user, exercise, *, exercise_id="", equipment="", other_name=""):
    """Turn a "Change variant" tap into an exercise.

    exercise_id: one of the family (checked: visible to the user and in the family);
    equipment: the family's variant with that equipment, or a new one created now;
    equipment "other" needs other_name ("weighted vest") and always means that name.
    """
    if exercise_id:
        chosen = family(user, exercise).filter(pk=exercise_id).first()
        if chosen is None:
            raise InvalidVariantChoice("Not a variant of this exercise.")
        return chosen
    if equipment not in Equipment.values:
        raise InvalidVariantChoice("Unknown equipment.")
    if equipment == Equipment.OTHER:
        if not other_name.strip():
            raise InvalidVariantChoice("Say what the equipment is.")
        return create_variant(user, exercise, equipment, label=other_name)
    existing = family(user, exercise).filter(equipment=equipment)
    # A built-in one first (shared, with its own photos), then the user's own.
    chosen = existing.order_by(F("owner").asc(nulls_first=True), "name").first()
    return chosen or create_variant(user, exercise, equipment)


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
