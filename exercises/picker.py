"""The mobile exercise picker, shared by the plan editor and the workout screen.

Each caller passes `select_base`: a URL ending in e.g. "?exercise=" to which the
chosen exercise's id is appended. Picking is therefore a plain link, which works
with or without JavaScript.
"""

from urllib.parse import urlencode

from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from .models import Category, Equipment, Level, MuscleGroup
from .services import (
    EQUIPMENT_SUGGESTIONS_SHOWN,
    WARMUP,
    equipment_suggestions,
    filter_options,
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


# The rows of chips, in order: (parameter, row label, "all" chip, choices). The last two
# rows sit under "More filters", open by themselves when one of them is chosen.
MAIN_ROWS = ("muscle", "equipment")
FILTER_ROWS = [
    (
        "muscle",
        _("Muscle group"),
        _("All muscles"),
        [c for c in MuscleGroup.choices if c[0] != MuscleGroup.OTHER],
    ),
    ("equipment", _("Equipment"), _("All equipment"), Equipment.choices),
    ("category", _("Type"), _("All types"), TYPE_CHOICES),
    ("level", _("Difficulty"), _("Any level"), Level.choices),
]
ALLOWED = {
    "muscle": set(MuscleGroup.values),
    "equipment": set(Equipment.values),
    "category": TYPE_VALUES,
    "level": set(Level.values),
}


def _chip_rows(options, chosen):
    """Each row with only the chips that give results, plus the chosen one (even at zero),
    so a choice can always be seen and changed. No counts on the chips."""
    rows = []
    for name, label, all_label, choices in FILTER_ROWS:
        shown = [
            (value, text)
            for value, text in choices
            if value == chosen[name] or options.has_results(name, value)
        ]
        rows.append(
            {
                "name": name,
                "label": label,
                "all_label": all_label,
                "choices": shown,
                "chosen": chosen[name],
            }
        )
    return rows


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
    chosen = {}
    for name in ALLOWED:
        value = request.GET.get(name, "")
        chosen[name] = value if value in ALLOWED[name] else ""
    muscle, equipment = chosen["muscle"], chosen["equipment"]
    level, category = chosen["level"], chosen["category"]

    results = search_exercises(request.user, query, muscle, equipment, level, category)
    options = filter_options(request.user, query, muscle, equipment, level, category)
    filtering = bool(normalize(query) or any(chosen.values()))
    # "More filters" stays open once opened, and opens by itself for a chosen type or level.
    more_open = request.GET.get("more") == "1" or bool(level or category)

    def url(**changes):
        """This picker with the same text and chips, except `changes` ("" removes one)."""
        params = {**(extra_params or {}), "q": query, **chosen, **changes}
        if more_open:
            params["more"] = "1"
        params = {name: value for name, value in params.items() if value}
        return f"{request.path}?{urlencode(params)}" if params else request.path

    labels = {name: dict(choices) for name, _label, _all, choices in FILTER_ROWS}
    chosen_filters = [
        {
            "label": labels[name][value],
            "remove_url": url(**{name: ""}),
            "without": options.without(name),
        }
        for name, value in chosen.items()
        if value
    ]
    # A muscle and equipment ("na smithie na dupę"): exercises for that muscle that could
    # also be done with it, each one tap from the user's own variant.
    parsed = parse_query(query)
    suggest_with = equipment or parsed.equipment
    also_with = equipment_suggestions(request.user, parsed.target, suggest_with)
    rows = _chip_rows(options, chosen)
    # Counted with the chips already (the same filter as the results): no extra query.
    results_count = options.total
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
        "level": level,
        "category": category,
        "main_rows": [r for r in rows if r["name"] in MAIN_ROWS],
        "more_rows": [r for r in rows if r["name"] not in MAIN_ROWS],
        "more_open": more_open,
        "chosen_filters": chosen_filters,
        "clear_url": url(muscle="", equipment="", category="", level=""),
        # Nothing found: each chip whose removal alone gives results, with how many.
        "way_out": [f for f in chosen_filters if f["without"]] if not results_count else [],
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
        # The chips come along out of band: chips without results disappear as you type.
        context["oob"] = True
        return render(request, "exercises/partials/picker_results.html", context)
    return render(request, "exercises/picker.html", context)
