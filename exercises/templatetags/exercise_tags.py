from django import template
from django.utils.translation import gettext as _

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
    main = ", ".join(str(labels[m]) for m in primary) or _("none")
    description = _("Main: %(muscles)s") % {"muscles": main}
    if secondary:
        helping = ", ".join(str(labels[m]) for m in secondary)
        description += ". " + _("Helping: %(muscles)s") % {"muscles": helping}
    return {"c": classes, "description": description}


@register.simple_tag
def change_variant_link(exercise, action, back):
    """{% change_variant_link exercise action_url back_url %}: the "Change variant" screen,
    which POSTs the choice to action_url; Cancel goes to back_url."""
    from exercises.views import change_variant_url

    return change_variant_url(exercise, action=action, back=back)
