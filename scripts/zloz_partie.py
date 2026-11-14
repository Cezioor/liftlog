"""Składa plik partii do przeglądu ze szkicu z samymi krokami PL.

Szkic: bloki "## <nr>. <nazwa angielska>" i pod nimi linie "PL n: …". Skrypt bierze z bazy
kroki EN, klucz i hash, więc EN w pliku partii jest zawsze identyczne z bazą.

    .venv/Scripts/python.exe manage.py shell -c "import sys;
        sys.argv=['x','--','<szkic>','<plik partii>','<nagłówek>'];
        exec(open('scripts/zloz_partie.py', encoding='utf-8').read())"
    (w jednej linii)
"""

import re
import sys
from pathlib import Path

from exercises.instructions_pl import english_hash, translation_key
from exercises.models import Exercise

args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
draft, target, title = Path(args[0]), Path(args[1]), args[2]
out = [
    f"# {title}",
    '# Format: "## nr. nazwa | polska nazwa | klucz | hash angielskich kroków", pary EN n / PL n.',
    '# Poprawki wpisz pod krokiem jako "POPRAWKA n: …" albo w sekcji UWAGI na końcu.',
    "",
]
for block in draft.read_text(encoding="utf-8").split("\n## ")[0:]:
    block = block.removeprefix("## ").strip()
    if not block:
        continue
    head, *lines = block.splitlines()
    number, name = re.match(r"(\S+)\.\s+(.*)", head).groups()
    exercise = Exercise.objects.get(owner=None, name=name.strip())
    pl = [m.group(1) for line in lines if (m := re.match(r"PL \d+: (.*)", line))]
    en = exercise.instructions
    if len(pl) != len(en):
        raise SystemExit(f"{name}: {len(pl)} kroków PL, {len(en)} EN")
    polish = exercise.aliases.split(",")[0].strip()
    key, digest = translation_key(exercise), english_hash(en)
    out.append(f"## {number}. {exercise.name} | {polish} | {key} | {digest}")
    for i, (e, p) in enumerate(zip(en, pl, strict=True), start=1):
        out += [f"EN {i}: {e}", f"PL {i}: {p}"]
    out.append("")
target.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Złożono {target.name}.")
