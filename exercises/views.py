from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ExerciseForm
from .models import Equipment, Exercise, MuscleGroup
from .services import find_by_name, search_exercises


@login_required
def exercise_list(request):
    query = request.GET.get("q", "").strip()
    exercises = search_exercises(request.user, query)
    return render(
        request,
        "exercises/exercise_list.html",
        {"exercises": exercises, "query": query},
    )


@login_required
def exercise_create(request):
    if request.method == "POST":
        form = ExerciseForm(request.POST, owner=request.user)
        if form.is_valid():
            exercise = form.save()
            messages.success(request, f"Added “{exercise.name}”.")
            return redirect("exercises:exercise_list")
    else:
        form = ExerciseForm(owner=request.user)
    return render(request, "exercises/exercise_form.html", {"form": form})


@login_required
def exercise_update(request, pk):
    # Only the user's own exercises: built-ins are shared, so nobody can edit them here.
    exercise = get_object_or_404(Exercise, pk=pk, owner=request.user)
    form = ExerciseForm(request.POST or None, instance=exercise, owner=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Saved “{exercise.name}”.")
        return redirect("exercises:exercise_list")
    return render(request, "exercises/exercise_form.html", {"form": form, "exercise": exercise})


@login_required
@require_POST
def exercise_quick_add(request):
    """The picker's "Add my own: «typed text»" button: create the exercise and select it.

    The muscle group / equipment filters chosen in the picker are used, otherwise
    "Other"; the user can fill in details later in the library.
    """
    name = request.POST.get("name", "").strip()[:100]
    next_url = request.POST.get("next", "")
    is_local = next_url.startswith("/") and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )
    if not name or not is_local:
        return HttpResponseBadRequest("Invalid exercise name or return address.")

    exercise = find_by_name(request.user, name)
    if exercise is None:
        muscle = request.POST.get("muscle", "")
        equipment = request.POST.get("equipment", "")
        exercise = Exercise.objects.create(
            owner=request.user,
            name=name,
            muscle_group=muscle if muscle in MuscleGroup.values else MuscleGroup.OTHER,
            equipment=equipment if equipment in Equipment.values else Equipment.OTHER,
            is_bodyweight=equipment == Equipment.BODYWEIGHT,
        )
        messages.success(
            request,
            f"Created “{exercise.name}”. You can set its details later in Exercises.",
        )
    return redirect(f"{next_url}{exercise.pk}")
