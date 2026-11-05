"""Stage 1.6: exercise types.

Written by hand on purpose: `category` (free-exercise-db's raw category) is *renamed* to
`source_category`, keeping its data. An auto-generated migration would drop the column
and add a new one, losing the values. Every other operation only adds columns with
defaults, so existing rows are not rewritten. The importer and seed_exercises fill the
new fields on the next build.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exercises", "0005_source_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="exercise",
            old_name="category",
            new_name="source_category",
        ),
        migrations.AlterField(
            model_name="exercise",
            name="source_category",
            field=models.CharField(blank=True, editable=False, max_length=30),
        ),
        migrations.AddField(
            model_name="exercise",
            name="category",
            field=models.CharField(
                choices=[
                    ("strength", "Strength"),
                    ("isometric", "Isometric"),
                    ("mobility", "Stretching / mobility"),
                    ("plyometric", "Plyometric"),
                    ("motor", "Motor control / balance"),
                    ("cardio", "Cardio"),
                    ("rehab", "Rehab"),
                ],
                default="strength",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="exercise",
            name="measurement",
            field=models.CharField(
                choices=[
                    ("weight_reps", "Weight × reps"),
                    ("reps", "Reps"),
                    ("time", "Time"),
                    ("distance_time", "Distance + time"),
                ],
                default="weight_reps",
                help_text="Which fields a set has: kg × reps, reps, time, or distance + time.",
                max_length=20,
                verbose_name="logged as",
            ),
        ),
        migrations.AddField(
            model_name="exercise",
            name="is_unilateral",
            field=models.BooleanField(
                default=False,
                help_text="Log left and right separately (e.g. single-leg exercises).",
                verbose_name="one side at a time",
            ),
        ),
    ]
