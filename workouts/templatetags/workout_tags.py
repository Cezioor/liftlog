from django import template

from workouts.services import format_kg

register = template.Library()


@register.filter
def kg(value):
    """{{ set.weight_kg|kg }} -> "62.5" (no trailing zeros)."""
    return format_kg(value)


@register.inclusion_tag("workouts/partials/exercise_card.html", takes_context=True)
def exercise_card(context, card):
    """{% exercise_card card %} renders one card from the dict built in views.build_card."""
    return {**card, "csrf_token": context.get("csrf_token"), "request": context.get("request")}
