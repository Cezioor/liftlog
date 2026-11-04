"""Add Exercise.progression_step_kg and fill it for existing rows.

Three steps, the usual way to add a required column to a table with data:
1. add the column as nullable, 2. fill it, 3. make it NOT NULL.
"""

from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def fill_steps(apps, schema_editor):
    # Rule copied from exercises.services.default_progression_step on purpose:
    # migrations must not import app code that may change later.
    Exercise = apps.get_model("exercises", "Exercise")
    lower = {"quads", "hamstrings", "glutes", "calves"}
    for exercise in Exercise.objects.all():
        if exercise.equipment == "dumbbell":
            step = Decimal("2")
        elif exercise.muscle_group in lower:
            step = Decimal("5")
        else:
            step = Decimal("2.5")
        exercise.progression_step_kg = step
        exercise.save(update_fields=["progression_step_kg"])


class Migration(migrations.Migration):
    dependencies = [
        ("exercises", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="progression_step_kg",
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.RunPython(fill_steps, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="exercise",
            name="progression_step_kg",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "How much weight to add when you hit the top of the rep range on every set."
                ),
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.25")),
                    django.core.validators.MaxValueValidator(Decimal("50")),
                ],
                verbose_name="progression step (kg)",
            ),
        ),
    ]
