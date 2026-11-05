from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.services import get_user_settings
from workouts.services import last_sets, personal_records, recently_used_exercises

from .forms import ExerciseForm
from .models import Equipment, Exercise, Muscle, MuscleGroup
from .picker import picker_response
from .services import find_by_name, muscles_for_map


@login_required
def exercise_list(request):
    """The exercise library: the same picker as in plans and workouts, linking to details."""
    return picker_response(
        request,
        title="Exercises",
        back_url=reverse("home"),
        select_base=reverse("exercises:exercise_list"),
        select_suffix="/",
        recent=recently_used_exercises(request.user),
        header_action=("+ Add", reverse("exercises:exercise_create")),
    )


@login_required
def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=pk)
    primary, secondary = muscles_for_map(exercise)
    labels = dict(Muscle.choices)
    return render(
        request,
        "exercises/exercise_detail.html",
        {
            "exercise": exercise,
            "primary_muscles": primary,
            "secondary_muscles": secondary,
            "primary_labels": [labels[m] for m in primary],
            "secondary_labels": [labels[m] for m in secondary],
            "last_sets": last_sets(request.user, exercise),
            "records": personal_records(request.user, exercise),
            "can_edit": exercise.owner_id == request.user.pk,
            "effort_scale": get_user_settings(request.user).effort_scale,
        },
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
    # Only "" or "/" may follow the id, so the redirect stays on the path chosen above.
    suffix = "/" if request.POST.get("suffix") == "/" else ""
    return redirect(f"{next_url}{exercise.pk}{suffix}")
