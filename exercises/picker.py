"""The mobile exercise picker, shared by the plan editor and the workout screen.

Each caller passes `select_base`: a URL ending in e.g. "?exercise=" to which the
chosen exercise's id is appended. Picking is therefore a plain link, which works
with or without JavaScript.
"""

from django.shortcuts import render

from .models import Equipment, Level, MuscleGroup
from .services import find_by_name, parse_query, search_exercises, variant_suggestion
from .text import normalize

RESULTS_LIMIT = 50


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
):
    """Render the picker. A result links to f"{select_base}{exercise.pk}{select_suffix}".

    header_action: optional (label, url) shown as a button next to the title.
    """
    query = request.GET.get("q", "").strip()[:100]
    muscle = request.GET.get("muscle", "")
    equipment = request.GET.get("equipment", "")
    level = request.GET.get("level", "")
    muscle = muscle if muscle in MuscleGroup.values else ""
    equipment = equipment if equipment in Equipment.values else ""
    level = level if level in Level.values else ""

    results = search_exercises(request.user, query, muscle, equipment, level)
    filtering = bool(normalize(query) or muscle or equipment or level)
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
    }
    if request.headers.get("HX-Target") == "picker-results":
        return render(request, "exercises/partials/picker_results.html", context)
    return render(request, "exercises/picker.html", context)
