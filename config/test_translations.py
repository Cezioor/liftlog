"""The Polish translations in locale/pl/LC_MESSAGES: complete, reviewed and compiled.

Workflow for every new text people see: gettext -> makemessages -l pl -> translate ->
compilemessages -> commit both django.po and django.mo (Render can't run gettext).
These tests fail when that chain was cut short:
- an empty or fuzzy entry (makemessages adds fuzzy guesses that nobody checked yet);
- a translation that loses or invents a %(placeholder)s (the page would crash);
- django.mo older than django.po (compilemessages was not run).
"""

import gettext
import re
from pathlib import Path

import polib
import pytest
from django.conf import settings

PO = Path(settings.BASE_DIR) / "locale" / "pl" / "LC_MESSAGES" / "django.po"
MO = PO.with_suffix(".mo")
PLACEHOLDER = re.compile(r"%\(\w+\)[sd]")


def _key(entry):
    return f"[{entry.msgctxt}] {entry.msgid}" if entry.msgctxt else entry.msgid


def _forms(entry):
    """[(source text, translation)] of an entry: one pair, or one per plural form."""
    if not entry.msgid_plural:
        return [(entry.msgid, entry.msgstr)]
    forms = sorted(entry.msgstr_plural.items())
    return [(entry.msgid if i == 0 else entry.msgid_plural, text) for i, text in forms]


def untranslated(catalog):
    return [_key(e) for e in catalog if any(not text for _, text in _forms(e))]


def fuzzy(catalog):
    return [_key(e) for e in catalog if "fuzzy" in e.flags]


def broken_placeholders(catalog):
    return [
        _key(e)
        for e in catalog
        for source, text in _forms(e)
        if text and set(PLACEHOLDER.findall(source)) != set(PLACEHOLDER.findall(text))
    ]


@pytest.fixture(scope="module")
def catalog():
    return polib.pofile(str(PO))


def test_every_text_has_a_translation(catalog):
    assert untranslated(catalog) == []


def test_no_translation_is_fuzzy(catalog):
    assert fuzzy(catalog) == []
    assert not catalog.metadata_is_fuzzy


def test_translations_keep_their_placeholders(catalog):
    assert broken_placeholders(catalog) == []


def test_plural_entries_have_every_polish_form(catalog):
    forms = int(re.search(r"nplurals=(\d+)", catalog.metadata["Plural-Forms"]).group(1))
    plural = [e for e in catalog if e.msgid_plural]

    assert plural, "the .po has plural entries (sets, reps)"
    assert [_key(e) for e in plural if len(e.msgstr_plural) != forms] == []


def test_the_compiled_mo_matches_the_po(catalog):
    with MO.open("rb") as file:
        compiled = gettext.GNUTranslations(file)._catalog

    stale = []
    for entry in catalog:
        if entry.obsolete:
            continue
        msgid = f"{entry.msgctxt}\x04{entry.msgid}" if entry.msgctxt else entry.msgid
        if entry.msgid_plural:
            found = [compiled.get((msgid, i)) for i in sorted(entry.msgstr_plural)]
            expected = [entry.msgstr_plural[i] for i in sorted(entry.msgstr_plural)]
        else:
            found, expected = compiled.get(msgid), entry.msgstr
        if found != expected:
            stale.append(_key(entry))
    assert stale == [], "run: python manage.py compilemessages --ignore=.venv"


def test_the_checks_catch_empty_fuzzy_and_broken_entries():
    """The checks above would really fail: a small catalog with each kind of problem."""
    catalog = polib.POFile()
    catalog.append(polib.POEntry(msgid="Rest", msgstr=""))
    catalog.append(polib.POEntry(msgid="Skip", msgstr="Pomiń", flags=["fuzzy"]))
    catalog.append(polib.POEntry(msgid="Log set %(number)s", msgstr="Zapisz serię %(nr)s"))
    catalog.append(
        polib.POEntry(
            msgid="%(done)s set",
            msgid_plural="%(done)s sets",
            msgstr_plural={0: "%(done)s seria", 1: "%(done)s serie", 2: ""},
        )
    )

    assert untranslated(catalog) == ["Rest", "%(done)s set"]
    assert fuzzy(catalog) == ["Skip"]
    assert broken_placeholders(catalog) == ["Log set %(number)s"]
