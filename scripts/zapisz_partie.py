"""Zapisuje zaakceptowaną partię tłumaczeń do exercises/data/instructions_pl.json.

Uruchomienie (lokalna baza musi mieć aktualne instrukcje: seed_exercises + import):
    .venv/Scripts/python.exe manage.py shell -c "import sys;
        sys.argv=['x','--','polskie_nazwy/instrukcje_partia_1.txt'[,'--auto']];
        exec(open('scripts/zapisz_partie.py', encoding='utf-8').read())"
    (w jednej linii)

Sprawdza, czy kroki EN w pliku są identyczne z bazą (inaczej przerywa), liczy hash
angielskich kroków i zapisuje kroki PL pod kluczem source_id (albo nazwą, gdy go nie ma).
Bloki z "[POZA PARTIĄ" w nagłówku są pomijane. --auto oznacza tłumaczenie automatyczne.
"""

import json
import re
import sys
from pathlib import Path

from exercises.instructions_pl import DATA_FILE, english_hash, translation_key
from exercises.models import Exercise

args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
batch, auto = Path(args[0]), "--auto" in args
text = batch.read_text(encoding="utf-8").split("\n# ====")[0]
data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
saved = 0
for block in text.split("\n## ")[1:]:
    head, *lines = block.splitlines()
    if "[POZA PARTIĄ" in head:
        continue
    name = re.sub(r"^\S+\.\s*", "", head.split(" | ")[0]).strip()
    exercise = Exercise.objects.get(owner=None, name=name)
    en = [m.group(2) for line in lines if (m := re.match(r"EN (\d+): (.*)", line))]
    pl = [m.group(2).strip() for line in lines if (m := re.match(r"PL (\d+): (.*)", line))]
    if en != exercise.instructions:
        raise SystemExit(f"{name}: kroki EN w pliku różnią się od bazy")
    if len(pl) != len(en) or not all(pl):
        raise SystemExit(f"{name}: liczba kroków PL się nie zgadza albo jest pusty krok")
    data[translation_key(exercise)] = {
        "name": exercise.name,
        "en_hash": english_hash(exercise.instructions),
        "auto": auto,
        "steps": pl,
    }
    saved += 1
DATA_FILE.parent.mkdir(exist_ok=True)
DATA_FILE.write_text(
    json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Zapisano {saved} ćwiczeń z {batch.name}; razem w pliku: {len(data)}.")
