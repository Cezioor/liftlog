from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExerciseForm
from .models import Exercise


@login_required
def exercise_list(request):
    exercises = Exercise.objects.visible_to(request.user)
    query = request.GET.get("q", "").strip()
    if query:
        exercises = exercises.filter(name__icontains=query)
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
