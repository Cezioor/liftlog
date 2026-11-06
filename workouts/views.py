import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Min
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from accounts.services import get_user_settings, ios_shortcut_url
from exercises.models import Exercise
from exercises.picker import picker_response
from exercises.views import change_variant_url, chosen_variant
from plans.models import Plan, PlanDay, PlanExercise

from . import services
from .forms import FinishWorkoutForm, WorkoutSetForm
from .models import Workout, WorkoutSet

DEFAULT_REST_SECONDS = 90


# --- helpers --------------------------------------------------------------


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _get_open_workout(request, pk):
    """A workout of this user that is still in progress (sets can only change there)."""
    return get_object_or_404(Workout, pk=pk, owner=request.user, finished_at__isnull=True)


def _get_own_set(request, pk):
    return get_object_or_404(
        WorkoutSet.objects.select_related("workout", "exercise"),
        pk=pk,
        workout__owner=request.user,
        workout__finished_at__isnull=True,
    )


def _plan_exercise_for(workout, exercise):
    return services.plan_exercise_for(workout, exercise)


def _workout_url(workout, exercise=None):
    url = reverse("workouts:workout_detail", args=[workout.pk])
    return f"{url}#ex-{exercise.pk}" if exercise else url


def _effort_scale(user):
    """How this user rates sets (simple / RIR / RPE); ratings are stored as RIR either way."""
    return get_user_settings(user).effort_scale


def _form_kwargs(exercise, scale):
    """The set form shows only the inputs that fit the exercise's type (Stage 1.6)."""
    return {
        "measurement": exercise.measurement,
        "unilateral": exercise.is_unilateral,
        "effort_scale": scale,
    }


def _add_set_form(exercise, scale, data=None, initial=None):
    # Unique HTML ids per card, because one page shows many of these forms.
    return WorkoutSetForm(
        data, initial=initial, auto_id=f"ex{exercise.pk}_%s", **_form_kwargs(exercise, scale)
    )


def _edit_set_form(workout_set, scale, data=None):
    weight = workout_set.weight_kg
    return WorkoutSetForm(
        data,
        instance=workout_set,
        initial={"weight_kg": services.format_kg(weight) if weight else ""},
        auto_id=f"set{workout_set.pk}_%s",
        **_form_kwargs(workout_set.exercise, scale),
    )


def build_card(workout, exercise, plan_exercise=None, form=None, edit_form=None, scale=None):
    """Everything the exercise card template needs."""
    scale = scale or _effort_scale(workout.owner)
    current = list(workout.sets.filter(exercise=exercise))
    previous = services.last_sets(workout.owner, exercise, exclude_workout=workout)
    rep_min = plan_exercise.rep_min if plan_exercise else None
    rep_max = plan_exercise.rep_max if plan_exercise else None
    hold_min = plan_exercise.hold_min_s if plan_exercise else None
    hold_max = plan_exercise.hold_max_s if plan_exercise else None
    hint = services.progression_hint(
        exercise, previous, rep_max=rep_max, hold_max=hold_max, rep_min=rep_min
    )
    defaults = services.next_set_defaults(
        current,
        previous,
        hint,
        rep_min,
        measurement=exercise.measurement,
        hold_min=hold_min,
        unilateral=exercise.is_unilateral,
    )
    # First time with this exercise: find the starting point (test hold / set, test weights).
    calibration = None
    if not previous:
        calibration = services.calibration(
            exercise, current, rep_min, rep_max, hold_min=hold_min, hold_max=hold_max
        )
        if calibration and calibration.defaults:
            defaults = calibration.defaults

    if form is None:
        form = _add_set_form(
            exercise,
            scale,
            initial={
                "weight_kg": services.format_kg(defaults.weight_kg),
                "reps": defaults.reps,
                "duration_seconds": defaults.duration_seconds,
                "distance_m": defaults.distance_m,
                "side": defaults.side,
                "is_warmup": defaults.is_warmup,
            },
        )

    # One row per set number: last time's set next to today's.
    target = plan_exercise.target_sets if plan_exercise else 0
    row_count = max(target, len(previous), len(current))
    rows = [
        {
            "number": i + 1,
            "previous": previous[i] if i < len(previous) else None,
            "current": current[i] if i < len(current) else None,
        }
        for i in range(row_count)
    ]

    return {
        "workout": workout,
        "exercise": exercise,
        "plan_exercise": plan_exercise,
        "rows": rows,
        "has_previous": bool(previous),
        "hint": hint,
        "calibration": calibration,
        "form": form,
        "edit_form": edit_form,
        "editing_id": edit_form.instance.pk if edit_form else None,
        "rest_seconds": plan_exercise.rest_seconds if plan_exercise else DEFAULT_REST_SECONDS,
        "done": len(current),
        "target": target,
        "measurement": exercise.measurement,
        "effort_scale": scale,
        "change_variant_url": change_variant_url(
            exercise,
            action=reverse("workouts:change_variant", args=[workout.pk, exercise.pk]),
            back=_workout_url(workout, exercise),
        ),
    }


def _card_response(request, card, status=200, rest=None):
    response = render(request, "workouts/partials/exercise_card.html", card, status=status)
    if rest:
        # HTMX turns this header into a "restStart" event that starts the timer.
        response["HX-Trigger"] = json.dumps({"restStart": rest})
    return response


def _rest_event(request, workout, exercise, seconds):
    """Details for the rest timer; adds the iOS Shortcuts link if the user enabled it."""
    rest = {"seconds": seconds}
    user_settings = get_user_settings(request.user)
    if user_settings.ios_shortcut_enabled and user_settings.ios_shortcut_name:
        return_url = request.build_absolute_uri(_workout_url(workout, exercise))
        rest["shortcutUrl"] = ios_shortcut_url(user_settings.ios_shortcut_name, seconds, return_url)
    return rest


# --- home and starting ----------------------------------------------------


@login_required
def home(request):
    active_plan = (
        Plan.objects.filter(owner=request.user, is_active=True).prefetch_related("days").first()
    )
    context = {
        "open_workout": Workout.objects.filter(
            owner=request.user, finished_at__isnull=True
        ).first(),
        "active_plan": active_plan,
        "recent_workouts": Workout.objects.filter(
            owner=request.user, finished_at__isnull=False
        ).select_related("plan_day")[:5],
    }
    return render(request, "home.html", context)


@login_required
@require_POST
def workout_start(request):
    existing = Workout.objects.filter(owner=request.user, finished_at__isnull=True).first()
    if existing:
        messages.info(request, _("You already have a workout in progress."))
        return redirect("workouts:workout_detail", pk=existing.pk)

    plan_day = None
    if request.POST.get("plan_day"):
        plan_day = get_object_or_404(PlanDay, pk=request.POST["plan_day"], plan__owner=request.user)
    workout = Workout.objects.create(owner=request.user, plan_day=plan_day)
    return redirect("workouts:workout_detail", pk=workout.pk)


# --- the workout screen ---------------------------------------------------


@login_required
def workout_detail(request, pk):
    workout = get_object_or_404(
        Workout.objects.select_related("plan_day"), pk=pk, owner=request.user
    )
    if workout.is_finished:
        return _workout_summary(request, workout)

    cards = []
    seen = set()
    scale = _effort_scale(request.user)
    if workout.plan_day:
        # "Only today" changes replace the plan's exercise for this workout.
        swaps = services.swapped_exercises(workout)
        for item in workout.plan_day.exercises.select_related("exercise"):
            exercise = swaps.get(item.pk, item.exercise)
            if exercise.pk not in seen:
                seen.add(exercise.pk)
                cards.append(build_card(workout, exercise, item, scale=scale))

    # Exercises added during the workout (not in the plan day), in the order first logged.
    extra_ids = list(
        workout.sets.exclude(exercise_id__in=seen)
        .values("exercise_id")
        .annotate(first=Min("pk"))
        .order_by("first")
        .values_list("exercise_id", flat=True)
    )
    extra = Exercise.objects.in_bulk(extra_ids)
    for exercise_id in extra_ids:
        seen.add(exercise_id)
        cards.append(build_card(workout, extra[exercise_id], scale=scale))

    # Chosen in the exercise picker: its card shows until the first set is logged.
    added_id = request.GET.get("add", "")
    if added_id.isdigit() and int(added_id) not in seen:
        added = Exercise.objects.visible_to(request.user).filter(pk=added_id).first()
        if added:
            cards.append(build_card(workout, added, scale=scale))

    return render(
        request,
        "workouts/workout_detail.html",
        {
            "workout": workout,
            "cards": cards,
            "finish_form": FinishWorkoutForm(instance=workout),
            "user_settings": get_user_settings(request.user),
        },
    )


@login_required
def add_exercise(request, pk):
    """Exercise picker for an open workout; picking redirects back with ?add=<id>."""
    workout = _get_open_workout(request, pk)
    exercise_id = request.GET.get("exercise", "")
    if exercise_id:
        if not exercise_id.isdigit():
            raise Http404
        exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=exercise_id)
        url = reverse("workouts:workout_detail", args=[workout.pk])
        return redirect(f"{url}?add={exercise.pk}#ex-{exercise.pk}")
    return picker_response(
        request,
        title=_("Add exercise"),
        back_url=_workout_url(workout),
        select_base=f"{request.path}?exercise=",
        recent=services.recently_used_exercises(request.user),
    )


def _workout_summary(request, workout):
    sets = workout.sets.select_related("exercise").order_by("pk")
    groups = {}
    for workout_set in sets:
        groups.setdefault(workout_set.exercise, []).append(workout_set)
    return render(
        request,
        "workouts/workout_summary.html",
        {
            "workout": workout,
            "groups": groups.items(),
            "effort_scale": _effort_scale(request.user),
        },
    )


@login_required
def exercise_card(request, pk, exercise_pk):
    """One exercise card on its own; HTMX uses it to cancel editing a set."""
    workout = _get_open_workout(request, pk)
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=exercise_pk)
    if not _is_htmx(request):
        return redirect(_workout_url(workout, exercise))
    return _card_response(
        request, build_card(workout, exercise, _plan_exercise_for(workout, exercise))
    )


@login_required
@require_POST
def set_create(request, pk, exercise_pk):
    workout = _get_open_workout(request, pk)
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=exercise_pk)
    plan_exercise = _plan_exercise_for(workout, exercise)
    form = _add_set_form(exercise, _effort_scale(request.user), request.POST)

    if not form.is_valid():
        if _is_htmx(request):
            return _card_response(request, build_card(workout, exercise, plan_exercise, form))
        messages.error(request, _("Check the weight and reps."))
        return redirect(_workout_url(workout, exercise))

    with transaction.atomic():
        workout_set = form.save(commit=False)
        workout_set.workout = workout
        workout_set.exercise = exercise
        last_order = workout.sets.filter(exercise=exercise).aggregate(m=Max("order"))["m"]
        workout_set.order = (last_order or 0) + 1
        workout_set.save()

    if _is_htmx(request):
        card = build_card(workout, exercise, plan_exercise)
        rest = _rest_event(request, workout, exercise, card["rest_seconds"])
        return _card_response(request, card, rest=rest)
    return redirect(_workout_url(workout, exercise))


@login_required
def set_update(request, pk):
    workout_set = _get_own_set(request, pk)
    workout, exercise = workout_set.workout, workout_set.exercise
    plan_exercise = _plan_exercise_for(workout, exercise)

    if request.method == "POST":
        form = _edit_set_form(workout_set, _effort_scale(request.user), request.POST)
        if form.is_valid():
            form.save()
            if _is_htmx(request):
                return _card_response(request, build_card(workout, exercise, plan_exercise))
            return redirect(_workout_url(workout, exercise))
    else:
        form = _edit_set_form(workout_set, _effort_scale(request.user))

    card = build_card(workout, exercise, plan_exercise, edit_form=form)
    if _is_htmx(request):
        return _card_response(request, card)
    return render(request, "workouts/set_edit.html", card)


@login_required
@require_POST
def set_delete(request, pk):
    workout_set = _get_own_set(request, pk)
    workout, exercise = workout_set.workout, workout_set.exercise
    with transaction.atomic():
        workout_set.delete()
        # Renumber the remaining sets so they stay 1, 2, 3, ...
        for number, remaining in enumerate(workout.sets.filter(exercise=exercise), start=1):
            if remaining.order != number:
                remaining.order = number
                remaining.save(update_fields=["order"])

    if _is_htmx(request):
        plan_exercise = _plan_exercise_for(workout, exercise)
        return _card_response(request, build_card(workout, exercise, plan_exercise))
    return redirect(_workout_url(workout, exercise))


@login_required
@require_POST
def change_variant(request, pk, exercise_pk):
    """The choice from "Change variant" on a card.

    A plan exercise: ask "Only today" or "Change in the plan too". An exercise added
    during the workout: just show the chosen variant's card. Logged sets stay put.
    """
    workout = _get_open_workout(request, pk)
    exercise = get_object_or_404(Exercise.objects.visible_to(request.user), pk=exercise_pk)
    chosen = chosen_variant(request, exercise)
    item = _plan_exercise_for(workout, exercise)
    if chosen == exercise:
        return redirect(_workout_url(workout, exercise))
    if item is None:
        url = reverse("workouts:workout_detail", args=[workout.pk])
        return redirect(f"{url}?add={chosen.pk}#ex-{chosen.pk}")
    return render(
        request,
        "workouts/change_variant_scope.html",
        {
            "workout": workout,
            "item": item,
            "current": exercise,
            "chosen": chosen,
            "logged": workout.sets.filter(exercise=exercise).count(),
        },
    )


@login_required
@require_POST
def apply_variant(request, pk, plan_exercise_pk):
    """ "Only today" / "Change in the plan too" for a plan exercise in this workout."""
    workout = _get_open_workout(request, pk)
    item = get_object_or_404(PlanExercise, pk=plan_exercise_pk, day_id=workout.plan_day_id)
    chosen = get_object_or_404(
        Exercise.objects.visible_to(request.user), pk=request.POST.get("exercise", "")
    )
    scope = request.POST.get("scope", "")
    same_movement = chosen.movement_id and chosen.movement_id == item.exercise.movement_id
    if scope not in (services.ONLY_TODAY, services.IN_PLAN_TOO) or not (
        same_movement or chosen.pk == item.exercise_id
    ):
        raise Http404("Not a variant of this plan exercise.")

    old_name = item.exercise.name
    services.change_variant_in_workout(workout, item, chosen, scope)
    if scope == services.IN_PLAN_TOO:
        messages.success(
            request,
            _("%(new)s replaces %(old)s in the plan too.") % {"new": chosen.name, "old": old_name},
        )
    else:
        messages.success(
            request,
            _("Only today: %(exercise)s. The plan stays as it was.") % {"exercise": chosen.name},
        )
    return redirect(_workout_url(workout, chosen))


@login_required
@require_POST
def workout_finish(request, pk):
    workout = _get_open_workout(request, pk)
    form = FinishWorkoutForm(request.POST, instance=workout)
    if form.is_valid():
        workout = form.save(commit=False)
        workout.finished_at = timezone.now()
        workout.save()
        messages.success(request, _("Workout saved. Nice work!"))
    return redirect("workouts:workout_detail", pk=workout.pk)


@login_required
@require_POST
def workout_discard(request, pk):
    workout = _get_open_workout(request, pk)
    workout.delete()
    messages.info(request, _("Workout discarded."))
    return redirect("home")
