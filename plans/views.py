from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

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
        messages.success(request, "Plan renamed.")
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
    messages.success(request, f"“{plan.name}” is now your active plan.")
    return _plan_redirect(plan)


@login_required
@require_POST
def plan_delete(request, pk):
    plan = _get_plan(request, pk)
    plan.delete()
    messages.success(request, f"Deleted “{plan.name}”.")
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
    messages.error(request, "Give the day a name.")
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
    messages.success(request, f"Deleted “{day.name}”.")
    return _plan_redirect(plan)


@login_required
@require_POST
def day_move(request, pk, direction):
    day = _get_day(request, pk)
    _move(day, day.plan.days.all(), direction)
    return _plan_redirect(day.plan, f"day-{day.pk}")


# --- exercises in a day ---------------------------------------------------


@login_required
def plan_exercise_create(request, day_pk):
    day = _get_day(request, day_pk)
    form = PlanExerciseForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.day = day
        item.order = _next_order(day.exercises.all())
        item.save()
        messages.success(request, f"Added {item.exercise.name} to {day.name}.")
        return _plan_redirect(day.plan, f"day-{day.pk}")
    return render(request, "plans/plan_exercise_form.html", {"form": form, "day": day})


@login_required
def plan_exercise_update(request, pk):
    item = _get_plan_exercise(request, pk)
    form = PlanExerciseForm(request.POST or None, instance=item, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return _plan_redirect(item.day.plan, f"day-{item.day_id}")
    return render(
        request,
        "plans/plan_exercise_form.html",
        {"form": form, "day": item.day, "item": item},
    )


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
