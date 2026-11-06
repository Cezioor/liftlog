"""Move "variant_of" links into Movement families.

Every base exercise that has variants gets a Movement; the base and all its variants
join it. Exercises themselves (ids, names, owners) and their workout history are not
changed; only the new `movement` column is filled. Built-in bases get a built-in family
(owner = null), a user's own base gets a family owned by that user.
"""

from django.db import migrations

EQUIPMENT_WORDS = {
    "barbell", "dumbbell", "dumbbells", "smith", "machine", "cable", "kettlebell",
    "kettlebells", "band", "bands", "ez", "bar",
}  # fmt: skip


def _family_name(name):
    words = [w for w in name.split() if w.lower().strip("-") not in EQUIPMENT_WORDS]
    return " ".join(words) or name


def variant_of_to_movements(apps, schema_editor=None, report=print):
    Exercise = apps.get_model("exercises", "Exercise")
    Movement = apps.get_model("exercises", "Movement")

    families = 0
    base_ids = set(
        Exercise.objects.exclude(variant_of=None).values_list("variant_of_id", flat=True)
    )
    for base in Exercise.objects.filter(pk__in=base_ids).order_by("pk"):
        movement = base.movement
        if movement is None:
            movement = Movement.objects.create(name=_family_name(base.name), owner=base.owner)
            base.movement = movement
            base.save(update_fields=["movement"])
            families += 1
        Exercise.objects.filter(variant_of=base).update(movement=movement)
    report(f"  variant families created from variant_of: {families}")


class Migration(migrations.Migration):
    dependencies = [("exercises", "0008_movements_and_equipment")]

    operations = [migrations.RunPython(variant_of_to_movements, migrations.RunPython.noop)]
