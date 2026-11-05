from django import template

from workouts.services import format_duration, format_kg, set_text

register = template.Library()


@register.filter
def kg(value):
    """{{ set.weight_kg|kg }} -> "62.5" (no trailing zeros)."""
    return format_kg(value)


@register.filter
def duration(seconds):
    """{{ 90|duration }} -> "1:30"."""
    return format_duration(seconds)


@register.filter(name="set_text")
def set_text_filter(workout_set, measurement):
    """{{ set|set_text:exercise.measurement }} -> "60 × 10", "12 reps", "45 s", "40 m in 0:35"."""
    return set_text(workout_set, measurement)


@register.filter
def set_text_long(workout_set, measurement):
    """Like set_text, with "kg" for weight × reps: "60 kg × 10"."""
    return set_text(workout_set, measurement, long=True)


@register.simple_tag
def set_label(workout_set, measurement, scale="", long=False):
    """{% set_label s measurement effort_scale %} -> "60 × 8 @RIR 2" or "60 × 8 · Hard"."""
    return set_text(workout_set, measurement, long=long, scale=scale or None)


@register.inclusion_tag("workouts/partials/exercise_card.html", takes_context=True)
def exercise_card(context, card):
    """{% exercise_card card %} renders one card from the dict built in views.build_card."""
    return {**card, "csrf_token": context.get("csrf_token"), "request": context.get("request")}
