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
