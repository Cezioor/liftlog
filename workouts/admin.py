from django.contrib import admin

from .models import Workout, WorkoutSet


class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 0


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("__str__", "owner", "started_at", "finished_at")
    list_filter = ("finished_at",)
    inlines = [WorkoutSetInline]
