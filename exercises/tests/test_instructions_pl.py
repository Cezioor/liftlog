"""Polish instructions: the data file, loading it, and what the exercise page shows."""

import re

import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse

from exercises.free_db import import_dataset, load_dataset
from exercises.instructions_pl import (
    apply_translations,
    english_hash,
    load_translations,
    shown_instructions,
    translation_key,
)
from exercises.models import Exercise
from exercises.services import create_variant, ensure_movement

EN = ["Lie on the bench.", "Press the bar up."]
PL = ["Połóż się na ławce.", "Wyciśnij sztangę w górę."]


def entry(steps=PL, english=EN, auto=False):
    return {"name": "x", "en_hash": english_hash(english), "auto": auto, "steps": steps}


@pytest.fixture
def bench(db):
    exercise = Exercise.objects.create(
        name="Test Bench Press", muscle_group="chest", equipment="barbell",
        source_id="Test_Bench", instructions=EN,
    )  # fmt: skip
    ensure_movement(exercise)
    return exercise


# --- the data file, against the real library --------------------------------------


@pytest.mark.django_db
def test_every_translation_matches_its_english_original():
    call_command("seed_exercises")
    import_dataset(load_dataset())
    call_command("seed_smith_variants")
    builtins = {translation_key(e): e for e in Exercise.objects.filter(owner=None)}
    translations = load_translations()

    assert translations
    for key, item in translations.items():
        assert key in builtins, f"{key}: no such built-in exercise"
        english = builtins[key].instructions
        steps = item["steps"]
        assert item["en_hash"] == english_hash(english), (
            f"{key}: the English steps changed after the translation"
        )
        assert len(steps) == len(english), f"{key}: {len(steps)} steps, {len(english)} in English"
        assert all(isinstance(s, str) and s.strip() for s in steps), f"{key}: an empty step"
        assert not re.search(r"[Ѐ-ӿ]", " ".join(steps)), f"{key}: Cyrillic"
        assert steps != english, f"{key}: not translated"
        assert isinstance(item["auto"], bool)


# --- loading -----------------------------------------------------------------------


@pytest.mark.django_db
def test_loading_writes_only_rows_that_changed(bench):
    other = Exercise.objects.create(name="Other", muscle_group="core", equipment="other")

    assert apply_translations({"Test_Bench": entry(auto=True)}) == (1, [])
    bench.refresh_from_db()
    assert (bench.instructions_pl, bench.instructions_pl_auto) == (PL, True)
    assert apply_translations({"Test_Bench": entry(auto=True)}) == (0, [])
    # Reviewed later: only the mark changes.
    assert apply_translations({"Test_Bench": entry()}) == (1, [])
    other.refresh_from_db()
    assert other.instructions_pl == []


@pytest.mark.django_db
def test_built_ins_without_a_source_id_are_keyed_by_name(db):
    plank = Exercise.objects.create(
        name="Side Plank Hold", muscle_group="core", equipment="bodyweight", instructions=EN
    )

    apply_translations({"Side Plank Hold": entry()})

    plank.refresh_from_db()
    assert plank.instructions_pl == PL


@pytest.mark.django_db
def test_a_translation_of_changed_english_steps_is_not_shown(bench):
    apply_translations({"Test_Bench": entry()})
    changed = ["Lie on the bench.", "Press the bar up slowly."]
    Exercise.objects.filter(pk=bench.pk).update(instructions=changed)

    assert apply_translations({"Test_Bench": entry()}) == (1, ["Test Bench Press"])
    bench.refresh_from_db()
    assert bench.instructions_pl == []


@pytest.mark.django_db
def test_users_exercises_are_never_loaded(user):
    mine = Exercise.objects.create(
        name="Test_Bench", muscle_group="chest", equipment="barbell", owner=user, instructions=EN
    )

    assert apply_translations({"Test_Bench": entry()}) == (0, [])
    mine.refresh_from_db()
    assert mine.instructions_pl == []


@pytest.mark.django_db
def test_the_command_reports_what_it_did(bench, capsys):
    call_command("load_polish_instructions")

    assert "0 rows updated" in capsys.readouterr().out  # the test exercise is not in the file


# --- what is shown -----------------------------------------------------------------


@pytest.mark.django_db
def test_polish_steps_in_polish_english_in_english(bench):
    apply_translations({"Test_Bench": entry()})
    bench.refresh_from_db()

    polish = shown_instructions(bench, "pl")
    assert (polish.steps, polish.automatic, polish.english_only) == (PL, False, False)
    english = shown_instructions(bench, "en")
    assert (english.steps, english.automatic, english.english_only) == (EN, False, False)


@pytest.mark.django_db
def test_an_unreviewed_translation_is_marked_automatic(bench):
    apply_translations({"Test_Bench": entry(auto=True)})
    bench.refresh_from_db()

    assert shown_instructions(bench, "pl").automatic
    assert not shown_instructions(bench, "en").automatic


def test_without_a_translation_english_with_a_note():
    exercise = Exercise(name="X", instructions=EN)

    shown = shown_instructions(exercise, "pl")

    assert (shown.steps, shown.english_only) == (EN, True)
    assert not shown_instructions(exercise, "en").english_only
    assert shown_instructions(Exercise(name="Y"), "pl").steps == []


@pytest.mark.django_db
def test_a_users_variant_shows_the_built_ins_translation(bench, user):
    variant = create_variant(user, bench, "dumbbell")
    apply_translations({"Test_Bench": entry(auto=True)})

    shown = shown_instructions(variant, "pl")

    assert (shown.steps, shown.automatic) == (PL, True)
    variant.refresh_from_db()
    assert (variant.instructions, variant.instructions_pl) == (EN, [])  # nothing copied
    # A corrected translation reaches the variant without touching it.
    fixed = ["Połóż się na ławce płaskiej.", PL[1]]
    apply_translations({"Test_Bench": entry(steps=fixed)})
    assert shown_instructions(variant, "pl").steps == fixed
    assert shown_instructions(variant, "en").steps == EN


@pytest.mark.django_db
def test_a_variant_with_edited_instructions_shows_the_users_text(bench, user):
    variant = create_variant(user, bench, "dumbbell")
    apply_translations({"Test_Bench": entry()})
    variant.instructions = ["My own cue: elbows at 45 degrees."]
    variant.save()

    shown = shown_instructions(variant, "pl")

    assert shown.steps == ["My own cue: elbows at 45 degrees."]
    assert not shown.english_only and not shown.automatic


@pytest.mark.django_db
def test_a_users_own_exercise_is_unchanged(user):
    mine = Exercise.objects.create(
        name="Meadows Row", muscle_group="back", equipment="barbell", owner=user,
        instructions=["Moje wskazówki."],
    )  # fmt: skip

    shown = shown_instructions(mine, "pl")

    assert (shown.steps, shown.english_only, shown.automatic) == (["Moje wskazówki."], False, False)


# --- the exercise page ------------------------------------------------------------


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


def _page(client, exercise, language):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
    return client.get(reverse("exercises:exercise_detail", args=[exercise.pk])).content.decode()


@pytest.mark.django_db
def test_the_page_shows_the_steps_in_the_page_language(logged_in, bench):
    apply_translations({"Test_Bench": entry(auto=True)})

    polish = _page(logged_in, bench, "pl")
    assert "Wyciśnij sztangę w górę." in polish and "Press the bar up." not in polish
    assert "Tłumaczenie automatyczne" in polish

    english = _page(logged_in, bench, "en")
    assert "Press the bar up." in english and "Wyciśnij" not in english
    assert "Automatic translation" not in english


@pytest.mark.django_db
def test_the_page_says_when_there_is_only_english(logged_in, bench):
    polish = _page(logged_in, bench, "pl")
    assert "Press the bar up." in polish
    assert "Instrukcja dostępna tylko po angielsku" in polish

    assert "Instructions available in English only" not in _page(logged_in, bench, "en")


@pytest.mark.django_db
def test_a_reviewed_translation_has_no_note(logged_in, bench):
    apply_translations({"Test_Bench": entry()})

    polish = _page(logged_in, bench, "pl")

    assert "Połóż się na ławce." in polish
    assert "Tłumaczenie automatyczne" not in polish and "tylko po angielsku" not in polish
