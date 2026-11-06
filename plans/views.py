from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from exercises.models import Exercise
from exercises.picker import picker_response
from exercises.views import chosen_variant
from workouts.services import recently_used_exercises

from .forms import PlanDayForm, PlanExerciseForm, PlanForm
from .models import Plan, PlanDay, PlanExercise

# --- helpers --------------------------------------------------------------


def _get_plan(request, pk):
    return get_object_or_404(Plan, pk=pk, owner=request.user)


def _get_day(request, pk):
    return get_object_or_404(PlanDay, pk=pk, plan__owner=request.user)


def _get_plan_exercise(request, pk):
    return get_object_or_404(PlanExercise, pk=pk, day__plan__owner=request.user)


def _next_order(queryset):
    return (queryset.aggregate(m=Max("order"))["m"] or 0) + 1


@transaction.atomic
def _move(obj, siblings, direction):
    """Swap `obj` with its neighbour above ("up") or below ("down")."""
    if direction not in ("up", "down"):
        raise Http404
    items = list(siblings)
    index = items.index(obj)
    target = index - 1 if direction == "up" else index + 1
    if not 0 <= target < len(items):
        return
    items[index], items[target] = items[target], items[index]
    # Renumber everything, which also repairs gaps or duplicate order values.
    for position, item in enumerate(items, start=1):
        if item.order != position:
            item.order = position
            item.save(update_fields=["order"])


def _plan_redirect(plan, anchor=""):
    url = reverse("plans:plan_detail", args=[plan.pk])
    return redirect(f"{url}#{anchor}" if anchor else url)


# --- plans ----------------------------------------------------------------


@login_required
def plan_list(request):
    plans = Plan.objects.filter(owner=request.user)
    return render(request, "plans/plan_list.html", {"plans": plans})


@login_required
def plan_create(request):
    form = PlanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        plan.owner = request.user
        # The first plan becomes active automatically.
        plan.is_active = not Plan.objects.filter(owner=request.user).exists()
        plan.save()
        return redirect("plans:plan_detail", pk=plan.pk)
    return render(request, "plans/plan_form.html", {"form": form})


@login_required
def plan_detail(request, pk):
    """The plan editor: rename the plan, manage its days and exercises."""
    plan = _get_plan(request, pk)
    rename_form = PlanForm(request.POST or None, instance=plan)
    if request.method == "POST" and rename_form.is_valid():
        rename_form.save()
        messages.success(request, _("Plan renamed."))
        return _plan_redirect(plan)
    days = plan.days.prefetch_related("exercises__exercise")
    return render(
        request,
        "plans/plan_detail.html",
        {"plan": plan, "days": days, "rename_form": rename_form, "day_form": PlanDayForm()},
    )


@login_required
@require_POST
def plan_activate(request, pk):
    plan = _get_plan(request, pk)
    plan.activate()
    messages.success(request, _("“%(plan)s” is now your active plan.") % {"plan": plan.name})
    return _plan_redirect(plan)


@login_required
@require_POST
def plan_delete(request, pk):
    plan = _get_plan(request, pk)
    plan.delete()
    messages.success(request, _("Deleted “%(name)s”.") % {"name": plan.name})
    return redirect("plans:plan_list")


# --- days -----------------------------------------------------------------


@login_required
@require_POST
def day_create(request, plan_pk):
    plan = _get_plan(request, plan_pk)
    form = PlanDayForm(request.POST)
    if form.is_valid():
        day = form.save(commit=False)
        day.plan = plan
        day.order = _next_order(plan.days.all())
        day.save()
        return _plan_redirect(plan, f"day-{day.pk}")
    messages.error(request, _("Give the day a name."))
    return _plan_redirect(plan)


@login_required
def day_update(request, pk):
    day = _get_day(request, pk)
    form = PlanDayForm(request.POST or None, instance=day)
    if request.method == "POST" and form.is_valid():
        form.save()
        return _plan_redirect(day.plan, f"day-{day.pk}")
    return render(request, "plans/day_form.html", {"form": form, "day": day})


@login_required
@require_POST
def day_delete(request, pk):
    day = _get_day(request, pk)
    plan = day.plan
    day.delete()
    messages.success(request, _("Deleted “%(name)s”.") % {"name": day.name})
    return _plan_redirect(plan)


@login_required
@require_POST
def day_move(request, pk, direction):
    day = _get_day(request, pk)
    _move(day, day.plan.days.all(), direction)
    return _plan_redirect(day.plan, f"day-{day.pk}")


# --- exercises in a day ---------------------------------------------------


def _picked_exercise(request):
    """The exercise chosen in the picker (?exercise=<id>), or None if not chosen yet.

    Only built-in exercises and the user's own ones can be picked; anything else is 404.
    """
    exercise_id = request.GET.get("exercise", "")
    if not exercise_id:
        return None
    if not exercise_id.isdigit():
        raise Http404
    return get_object_or_404(Exercise.objects.visible_to(request.user), pk=exercise_id)


def _exercise_picker(request, day, extra_params=None):
    # extra_params (e.g. pick=1) keep the picker open while searching; the result
    # links leave them out, so tapping a result goes on to the sets/reps form.
    return picker_response(
        request,
        title=_("Add to %(day)s") % {"day": day.name} if not extra_params else _("Change exercise"),
        back_url=f"{reverse('plans:plan_detail', args=[day.plan_id])}#day-{day.pk}",
        select_base=f"{request.path}?exercise=",
        recent=recently_used_exercises(request.user),
        extra_params=extra_params,
    )


@login_required
def plan_exercise_create(request, day_pk):
    """Step 1: pick an exercise (picker). Step 2: sets, reps and rest for it."""
    day = _get_day(request, day_pk)
    exercise = _picked_exercise(request)
    if exercise is None:
        return _exercise_picker(request, day)

    form = PlanExerciseForm(request.POST or None, measurement=exercise.measurement)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.day = day
        item.exercise = exercise
        item.order = _next_order(day.exercises.all())
        item.save()
        messages.success(
            request,
            _("Added %(exercise)s to %(day)s.") % {"exercise": exercise.name, "day": day.name},
        )
        return _plan_redirect(day.plan, f"day-{day.pk}")
    return render(
        request,
        "plans/plan_exercise_form.html",
        {"form": form, "day": day, "exercise": exercise, "change_url": request.path},
    )


@login_required
def plan_exercise_update(request, pk):
    item = _get_plan_exercise(request, pk)
    if request.GET.get("pick"):
        return _exercise_picker(request, item.day, extra_params={"pick": "1"})

    # A different exercise may come back from the picker as ?exercise=<id>.
    exercise = _picked_exercise(request) or item.exercise
    form = PlanExerciseForm(request.POST or None, instance=item, measurement=exercise.measurement)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.exercise = exercise
        item.save()
        return _plan_redirect(item.day.plan, f"day-{item.day_id}")
    return render(
        request,
        "plans/plan_exercise_form.html",
        {
            "form": form,
            "day": item.day,
            "item": item,
            "exercise": exercise,
            "change_url": f"{request.path}?pick=1",
        },
    )


@login_required
@require_POST
def plan_exercise_change_variant(request, pk):
    """ "Change variant" in the plan editor: same targets, other variant of the movement."""
    item = _get_plan_exercise(request, pk)
    old = item.exercise
    item.exercise = chosen_variant(request, old)
    item.save(update_fields=["exercise"])
    if item.exercise != old:
        messages.success(
            request,
            _("%(old)s → %(new)s in the plan.") % {"old": old.name, "new": item.exercise.name},
        )
    return _plan_redirect(item.day.plan, f"day-{item.day_id}")


@login_required
@require_POST
def plan_exercise_delete(request, pk):
    item = _get_plan_exercise(request, pk)
    day = item.day
    item.delete()
    return _plan_redirect(day.plan, f"day-{day.pk}")


@login_required
@require_POST
def plan_exercise_move(request, pk, direction):
    item = _get_plan_exercise(request, pk)
    _move(item, item.day.exercises.all(), direction)
    return _plan_redirect(item.day.plan, f"day-{item.day_id}")


@login_required
def add_to_plan(request, exercise_pk):
    """From an exercise's page: choose the plan day, then the usual sets/reps form."""
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=exercise_pk)
    plans = Plan.objects.filter(owner=request.user).prefetch_related("days")
    return render(request, "plans/add_to_plan.html", {"exercise": exercise, "plans": plans})
