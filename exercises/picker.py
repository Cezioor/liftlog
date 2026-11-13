"""The mobile exercise picker, shared by the plan editor and the workout screen.

Each caller passes `select_base`: a URL ending in e.g. "?exercise=" to which the
chosen exercise's id is appended. Picking is therefore a plain link, which works
with or without JavaScript.
"""

from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from .models import Category, Equipment, Exercise, Level, MuscleGroup
from .services import (
    EQUIPMENT_SUGGESTIONS_SHOWN,
    WARMUP,
    equipment_suggestions,
    find_by_name,
    parse_query,
    search_exercises,
    variant_suggestion,
)
from .text import normalize

RESULTS_LIMIT = 50

# Heading of the suggestions under "ćwiczenie na smithie na dupę"-like results, with the
# right Polish preposition and case for each piece of equipment.
ALSO_WITH = {
    Equipment.SMITH: _("You can also do these on the Smith machine"),
    Equipment.BARBELL: _("You can also do these with a barbell"),
    Equipment.DUMBBELL: _("You can also do these with dumbbells"),
    Equipment.KETTLEBELL: _("You can also do these with a kettlebell"),
    Equipment.CABLE: _("You can also do these on a cable"),
    Equipment.BAND: _("You can also do these with a resistance band"),
}


# The "Type" filter: categories plus the warm-up goal. Rehab is not offered: it comes
# with the rehab mode of Stage 2.
TYPE_CHOICES = [
    (Category.STRENGTH, Category.STRENGTH.label),
    (WARMUP, _("Warm-up")),
    (Category.MOBILITY, Category.MOBILITY.label),
    (Category.ISOMETRIC, Category.ISOMETRIC.label),
    (Category.PLYOMETRIC, Category.PLYOMETRIC.label),
    (Category.MOTOR, Category.MOTOR.label),
    (Category.CARDIO, Category.CARDIO.label),
]
TYPE_VALUES = {value for value, _label in TYPE_CHOICES}

# Tiles on the untouched exercise library: one tap filters by goal.
GOAL_TILES = [
    (Category.STRENGTH, pgettext_lazy("goal tile", "Strength")),
    (WARMUP, _("Warm-up")),
    (Category.MOBILITY, _("Stretching")),
    (Category.MOTOR, Category.MOTOR.label),
    (Category.CARDIO, _("Cardio")),
]


def _type_choices(user):
    """The "Type" choices that have exercises (no chip that always shows nothing)."""
    visible = Exercise.objects.visible_to(user)
    used = set(visible.values_list("category", flat=True).distinct())
    if visible.filter(search_text__contains="rozgrzewk").exists():
        used.add(WARMUP)
    return [(value, label) for value, label in TYPE_CHOICES if value in used]


def picker_response(
    request,
    *,
    select_base,
    title,
    back_url,
    recent=(),
    extra_params=None,
    select_suffix="",
    header_action=None,
    goal_tiles=False,
):
    """Render the picker. A result links to f"{select_base}{exercise.pk}{select_suffix}".

    header_action: optional (label, url) shown as a button next to the title.
    goal_tiles: show the goal tiles (Strength, Warm-up…) while nothing is chosen yet.
    """
    query = request.GET.get("q", "").strip()[:100]
    muscle = request.GET.get("muscle", "")
    equipment = request.GET.get("equipment", "")
    level = request.GET.get("level", "")
    muscle = muscle if muscle in MuscleGroup.values else ""
    equipment = equipment if equipment in Equipment.values else ""
    level = level if level in Level.values else ""
    category = request.GET.get("category", "")
    category = category if category in TYPE_VALUES else ""

    results = search_exercises(request.user, query, muscle, equipment, level, category)
    filtering = bool(normalize(query) or muscle or equipment or level or category)
    # A muscle and equipment ("na smithie na dupę"): exercises for that muscle that could
    # also be done with it, each one tap from the user's own variant.
    parsed = parse_query(query)
    suggest_with = equipment or parsed.equipment
    also_with = equipment_suggestions(request.user, parsed.target, suggest_with)
    results_count = results.count()
    context = {
        "title": title,
        "back_url": back_url,
        "select_base": select_base,
        "select_suffix": select_suffix,
        "header_action": header_action,
        "extra_params": extra_params or {},
        "query": query,
        "muscle": muscle,
        "equipment": equipment,
        "muscle_choices": [c for c in MuscleGroup.choices if c[0] != MuscleGroup.OTHER],
        "equipment_choices": Equipment.choices,
        "level": level,
        "level_choices": Level.choices,
        "category": category,
        "type_choices": _type_choices(request.user),
        "goal_tiles": GOAL_TILES if goal_tiles and not filtering else [],
        "results": results[:RESULTS_LIMIT],
        "results_count": results_count,
        "filtering": filtering,
        # "Recently used" only on the untouched picker; once you type, results matter.
        "recent": [] if filtering else list(recent),
        # Offer "Add my own: …" unless an exercise with exactly that name exists.
        "quick_add_name": query if query and not find_by_name(request.user, query) else "",
        # Equipment for "Add my own": the chip, else a word in the query ("… kettlebell").
        "quick_add_equipment": equipment or parse_query(query).equipment,
        # "Add variant: «Step-up» — Smith machine" when the movement exists without it.
        "variant": variant_suggestion(request.user, query) if query else None,
        "also_with": also_with[:EQUIPMENT_SUGGESTIONS_SHOWN],
        "also_with_more": also_with[EQUIPMENT_SUGGESTIONS_SHOWN:],
        "also_with_heading": ALSO_WITH.get(suggest_with, "") if also_with else "",
    }
    if request.headers.get("HX-Target") == "picker-results":
        return render(request, "exercises/partials/picker_results.html", context)
    return render(request, "exercises/picker.html", context)
