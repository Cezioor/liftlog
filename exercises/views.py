from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.services import get_user_settings
from workouts.services import last_sets, personal_records, recently_used_exercises

from .forms import ExerciseForm
from .models import Equipment, Exercise, Muscle, MuscleGroup
from .picker import picker_response
from .services import (
    InvalidVariantChoice,
    choose_variant,
    create_variant,
    family,
    find_by_name,
    muscles_for_map,
    variant_choices,
)


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
            # Other equipment, same movement: built-in ones and the user's own.
            "variants": family(request.user, exercise).exclude(pk=exercise.pk),
            "change_variant_url": change_variant_url(
                exercise,
                action=reverse("exercises:variant_open", args=[exercise.pk]),
                back=request.path,
            ),
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


def change_variant_url(exercise, *, action, back):
    """Link to the "Change variant" screen; the choice is POSTed to `action`."""
    query = urlencode({"action": action, "back": back})
    return f"{reverse('exercises:change_variant', args=[exercise.pk])}?{query}"


def _local_url(request, url):
    """`url` if it points at this site (never elsewhere), else None."""
    is_local = url.startswith("/") and url_has_allowed_host_and_scheme(
        url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )
    return url if is_local else None


@login_required
def change_variant(request, pk):
    """ "Change variant": the movement's variants first, then equipment without one.

    Shared by the plan editor, the workout screen and the exercise page. Each option is
    a small form POSTing `exercise` (an existing variant) or `equipment` (+ `other_name`
    for "Other…") to `action`, which decides what changing means there.
    """
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=pk)
    action = _local_url(request, request.GET.get("action", ""))
    back = _local_url(request, request.GET.get("back", "")) or reverse(
        "exercises:exercise_detail", args=[exercise.pk]
    )
    if action is None:
        return HttpResponseBadRequest("Invalid action address.")
    return render(
        request,
        "exercises/change_variant.html",
        {"choices": variant_choices(request.user, exercise), "action": action, "back": back},
    )


def chosen_variant(request, exercise):
    """The exercise picked on the "Change variant" screen (a POST to an `action`).

    Creates the variant when new equipment was picked. Raises Http404 for anything
    that isn't a valid choice for this user.
    """
    try:
        return choose_variant(
            request.user,
            exercise,
            exercise_id=request.POST.get("exercise", ""),
            equipment=request.POST.get("equipment", ""),
            other_name=request.POST.get("other_name", "")[:60],
        )
    except InvalidVariantChoice as error:
        raise Http404(str(error)) from error


@login_required
@require_POST
def variant_open(request, pk):
    """ "Change variant" from the exercise page: open the chosen variant's page."""
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=pk)
    chosen = chosen_variant(request, exercise)
    return redirect("exercises:exercise_detail", pk=chosen.pk)


def _picker_return_url(request):
    """The picker's return address from the form, or None if it isn't on this site."""
    return _local_url(request, request.POST.get("next", ""))


def _select(request, next_url, exercise):
    # Only "" or "/" may follow the id, so the redirect stays on the path checked above.
    suffix = "/" if request.POST.get("suffix") == "/" else ""
    return redirect(f"{next_url}{exercise.pk}{suffix}")


@login_required
@require_POST
def exercise_variant_create(request, pk):
    """The picker's "Add variant: «Step-up» — Smith machine": create it and select it."""
    base = get_object_or_404(Exercise.objects.visible_to(request.user), pk=pk)
    equipment = request.POST.get("equipment", "")
    next_url = _picker_return_url(request)
    if equipment not in Equipment.values or next_url is None:
        return HttpResponseBadRequest("Invalid equipment or return address.")
    variant = create_variant(request.user, base, equipment)
    messages.success(request, f"Created “{variant.name}”, with its own history and records.")
    return _select(request, next_url, variant)


@login_required
@require_POST
def exercise_quick_add(request):
    """The picker's "Add my own: «typed text»" button: create the exercise and select it.

    The muscle group / equipment filters chosen in the picker are used, otherwise
    "Other"; the user can fill in details later in the library.
    """
    name = request.POST.get("name", "").strip()[:100]
    next_url = _picker_return_url(request)
    if not name or next_url is None:
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
    return _select(request, next_url, exercise)
