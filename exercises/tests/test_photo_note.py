"""The note under the photos: what they show when it is not exactly this exercise."""

import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse

from exercises.free_db import import_dataset, load_dataset
from exercises.instructions_pl import shown_photo_note
from exercises.models import Exercise
from exercises.seed_data import PHOTO_NOTES
from exercises.services import create_variant, ensure_movement
from exercises.smith_variants import (
    FREE_WEIGHT_PHOTO_NOTE,
    OTHER_BASE_PHOTO_NOTE,
    PHOTO_SOURCES,
    SMITH_VARIANTS,
)

EN, PL = "The photos show the one-arm version.", "Zdjęcia pokazują wersję jednorącz."


@pytest.fixture
def swing(db):
    exercise = Exercise.objects.create(
        name="Test Swing", muscle_group="glutes", equipment="kettlebell",
        images=["Swing/0.jpg", "Swing/1.jpg"], instructions=["Swing it."],
        photo_note=EN, photo_note_pl=PL,
    )  # fmt: skip
    ensure_movement(exercise)
    return exercise


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


def _page(client, exercise, language):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
    return client.get(reverse("exercises:exercise_detail", args=[exercise.pk])).content.decode()


def test_the_note_follows_the_page_language(swing):
    assert shown_photo_note(swing, "en") == EN
    assert shown_photo_note(swing, "pl") == PL


def test_no_note_without_photos_or_without_a_note():
    assert shown_photo_note(Exercise(name="X", photo_note=EN), "en") == ""  # no photos
    assert shown_photo_note(Exercise(name="Y", images=["Y/0.jpg"]), "pl") == ""


@pytest.mark.django_db
def test_the_page_shows_the_note_under_the_photos_not_as_a_step(logged_in, swing):
    polish = _page(logged_in, swing, "pl")

    assert PL in polish and EN not in polish
    assert polish.index("</figure>") < polish.index(PL) < polish.index('<ol class="steps">')
    assert f"<li>{PL}</li>" not in polish
    assert EN in _page(logged_in, swing, "en")


@pytest.mark.django_db
def test_a_users_variant_with_the_same_photos_shows_the_note(swing, user):
    variant = create_variant(user, swing, "dumbbell")

    assert shown_photo_note(variant, "pl") == PL
    variant.refresh_from_db()
    assert (variant.photo_note, variant.photo_note_pl) == ("", "")  # nothing copied

    variant.images = []
    assert shown_photo_note(variant, "pl") == ""


@pytest.mark.django_db
def test_the_library_keeps_photo_notes_out_of_the_steps():
    call_command("seed_exercises")
    import_dataset(load_dataset())
    call_command("seed_smith_variants")

    for name, (english, polish) in PHOTO_NOTES.items():
        exercise = Exercise.objects.get(owner=None, name=name)
        assert (exercise.photo_note, exercise.photo_note_pl) == (english, polish), name
        assert exercise.images, name
    steps = [s for e in Exercise.objects.filter(owner=None) for s in e.instructions]
    assert not [s for s in steps if s.startswith("The photos show")]

    # Smith variants with the photos of a free-weight base share one note.
    noted = Exercise.objects.filter(owner=None, photo_note=FREE_WEIGHT_PHOTO_NOTE[0])
    assert noted.count() == 23
    assert all(e.equipment == "smith" and e.images for e in noted)
    assert {e.photo_note_pl for e in noted} == {FREE_WEIGHT_PHOTO_NOTE[1]}
    for name, base_name, *_ in SMITH_VARIANTS:
        variant = Exercise.objects.get(owner=None, name=name)
        if not base_name:
            assert (variant.images, variant.photo_note) == ([], ""), name
        if name in PHOTO_SOURCES:
            # Photos of the same exercise under another name, so nothing to explain.
            source = Exercise.objects.get(owner=None, name=PHOTO_SOURCES[name])
            assert (variant.images, variant.photo_note) == (source.images, ""), name
            assert variant.images, name
    # A base done on a machine or without weights: another note.
    others = Exercise.objects.filter(owner=None, photo_note=OTHER_BASE_PHOTO_NOTE[0])
    assert {e.name for e in others} == {
        "Smith Machine Donkey Calf Raise",
        "Smith Machine Incline Push-up",
        "Smith Machine Inverted Row",
    }
    assert {e.photo_note_pl for e in others} == {
        "Zdjęcia pokazują ten sam ruch bez suwnicy Smitha."
    }
