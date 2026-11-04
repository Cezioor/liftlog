from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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
