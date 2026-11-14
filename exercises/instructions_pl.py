"""Polish instructions for built-in exercises ("Next up" 6).

The translations live in exercises/data/instructions_pl.json, one entry per exercise:
{"name": ..., "en_hash": ..., "auto": bool, "steps": [...]}, keyed by the exercise's
source_id (free-exercise-db) or, for our own built-ins without one, by its name.
en_hash is the hash of the English steps the translation was made from, so a changed
English original shows up in the tests instead of silently keeping an old translation.
The vocabulary follows exercises/data/glossary_pl.md.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "instructions_pl.json"


def english_hash(steps):
    """A short, stable hash of a list of English steps."""
    text = json.dumps(list(steps), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def translation_key(exercise):
    return exercise.source_id or exercise.name


def load_translations(path=DATA_FILE):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def apply_translations(translations=None):
    """Copy the file's Polish steps onto the built-in exercises; returns (updated, stale).

    Only rows whose Polish steps or "auto" mark differ are written. A translation whose
    English original changed since (another en_hash) is not shown: the exercise falls
    back to English until it is translated again (the tests catch this before a deploy).
    A built-in that is no longer in the file loses its Polish steps.
    """
    from .models import Exercise

    if translations is None:
        translations = load_translations()
    changed, stale = [], []
    fields = ["name", "source_id", "instructions", "instructions_pl", "instructions_pl_auto"]
    for exercise in Exercise.objects.filter(owner__isnull=True).only(*fields):
        entry = translations.get(translation_key(exercise))
        steps, auto = [], False
        if entry:
            if entry["en_hash"] == english_hash(exercise.instructions):
                steps, auto = list(entry["steps"]), bool(entry["auto"])
            else:
                stale.append(exercise.name)
        if (exercise.instructions_pl, exercise.instructions_pl_auto) != (steps, auto):
            exercise.instructions_pl, exercise.instructions_pl_auto = steps, auto
            changed.append(exercise)
    Exercise.objects.bulk_update(changed, ["instructions_pl", "instructions_pl_auto"])
    return len(changed), stale


@dataclass(frozen=True)
class ShownInstructions:
    steps: list
    automatic: bool = False  # Polish, translated automatically and not reviewed yet
    english_only: bool = False  # Polish was asked for, but there is no translation


def _in_language(exercise, language):
    if not (language or "").startswith("pl"):
        return ShownInstructions(list(exercise.instructions))
    if exercise.instructions_pl:
        return ShownInstructions(list(exercise.instructions_pl), exercise.instructions_pl_auto)
    return ShownInstructions(list(exercise.instructions), english_only=True)


def shown_instructions(exercise, language):
    """The steps to show for "How to do it" in the page's language.

    Built-ins: Polish steps when they exist, else English with a note. A user's own
    exercise keeps its own text. A user's variant has a copy of a built-in's English
    steps and no Polish of its own: while that copy is identical to the steps of a
    built-in of the same family, that built-in's translation is shown, so corrections
    reach variants and users' data never changes. Once the user edits the text, it is theirs.
    """
    from .models import Exercise

    if not exercise.instructions:
        return ShownInstructions([])
    if exercise.owner_id is None:
        return _in_language(exercise, language)
    if exercise.movement_id and (language or "").startswith("pl"):
        family = Exercise.objects.filter(owner__isnull=True, movement_id=exercise.movement_id)
        for builtin in family.order_by("pk"):
            if builtin.instructions == exercise.instructions:
                return _in_language(builtin, language)
    return ShownInstructions(list(exercise.instructions))


def shown_photo_note(exercise, language):
    """The note under the photos ("The photos show…"), in the page's language.

    A user's variant has a copy of a built-in's photos: while they are the same as those
    of a built-in of its family, that built-in's note is shown.
    """
    from .models import Exercise

    source = exercise
    if exercise.owner_id is not None:
        source = None
        if exercise.movement_id and exercise.images:
            family = Exercise.objects.filter(owner__isnull=True, movement_id=exercise.movement_id)
            source = next((b for b in family.order_by("pk") if b.images == exercise.images), None)
    if source is None or not source.images:
        return ""
    if (language or "").startswith("pl") and source.photo_note_pl:
        return source.photo_note_pl
    return source.photo_note
