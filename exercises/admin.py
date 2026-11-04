from django.contrib import admin

from .models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "equipment", "is_bodyweight", "owner")
    list_filter = ("muscle_group", "equipment", "is_bodyweight")
    search_fields = ("name",)
