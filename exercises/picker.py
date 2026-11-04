"""The mobile exercise picker, shared by the plan editor and the workout screen.

Each caller passes `select_base`: a URL ending in e.g. "?exercise=" to which the
chosen exercise's id is appended. Picking is therefore a plain link, which works
with or without JavaScript.
"""

from django.shortcuts import render

from .models import Equipment, MuscleGroup
from .services import find_by_name, search_exercises
from .text import normalize

RESULTS_LIMIT = 50


def picker_response(request, *, select_base, title, back_url, recent=(), extra_params=None):
    query = request.GET.get("q", "").strip()[:100]
    muscle = request.GET.get("muscle", "")
    equipment = request.GET.get("equipment", "")
    muscle = muscle if muscle in MuscleGroup.values else ""
    equipment = equipment if equipment in Equipment.values else ""

    results = search_exercises(request.user, query, muscle, equipment)
    filtering = bool(normalize(query) or muscle or equipment)
    context = {
        "title": title,
        "back_url": back_url,
        "select_base": select_base,
        "extra_params": extra_params or {},
        "query": query,
        "muscle": muscle,
        "equipment": equipment,
        "muscle_choices": [c for c in MuscleGroup.choices if c[0] != MuscleGroup.OTHER],
        "equipment_choices": Equipment.choices,
        "results": results[:RESULTS_LIMIT],
        "results_count": results.count(),
        "filtering": filtering,
        # "Recently used" only on the untouched picker; once you type, results matter.
        "recent": [] if filtering else list(recent),
        # Offer "Add my own: …" unless an exercise with exactly that name exists.
        "quick_add_name": query if query and not find_by_name(request.user, query) else "",
    }
    if request.headers.get("HX-Target") == "picker-results":
        return render(request, "exercises/partials/picker_results.html", context)
    return render(request, "exercises/picker.html", context)
