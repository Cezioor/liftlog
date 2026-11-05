from django import template

from exercises.models import Muscle

register = template.Library()


@register.inclusion_tag("exercises/partials/muscle_map.html")
def muscle_map(primary, secondary):
    """Front/back SVG body; primary muscles strong, secondary lighter.

    `c` maps each muscle (spaces as underscores, e.g. "lower_back") to a CSS class.
    """
    classes = {}
    for muscle in Muscle.values:
        key = muscle.replace(" ", "_")
        if muscle in primary:
            classes[key] = "m-primary"
        elif muscle in secondary:
            classes[key] = "m-secondary"
        else:
            classes[key] = ""
    labels = dict(Muscle.choices)
    description = "Main: " + (", ".join(labels[m] for m in primary) or "none")
    if secondary:
        description += ". Helping: " + ", ".join(labels[m] for m in secondary)
    return {"c": classes, "description": description}
