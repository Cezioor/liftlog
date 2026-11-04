from django.contrib import admin

from .models import Plan, PlanDay, PlanExercise


class PlanDayInline(admin.TabularInline):
    model = PlanDay
    extra = 0


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active", "created_at")
    inlines = [PlanDayInline]


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 0


@admin.register(PlanDay)
class PlanDayAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "order")
    inlines = [PlanExerciseInline]
