"""The owner's decisions on movement families (see exercises/movements.py).

A family found by name is doubtful when its members share equipment, work different
muscle groups, belong to different categories or differ in one side vs both sides. Such
a group is applied only after its key is listed in CONFIRMED_GROUPS. Keys in
REJECTED_GROUPS are never grouped (also usable for clear groups that turn out wrong).
MANUAL_GROUPS joins exercises whose names differ by more than equipment words.

`python manage.py group_movements --pending` lists the groups still waiting.
"""

# Decided by the owner on 2026-11-06.
CONFIRMED_GROUPS: set[str] = {
    "step up",
    "lunge",
    "floor press",
    "one arm floor press",
    "shrug",
    "upright row",
    "clean",
    "hang clean",
    "bent arm pullover",
    "hip adduction",
    "preacher curl",
    "decline press",
}

REJECTED_GROUPS: set[str] = {
    "windmill",  # Kettlebell Windmill (strength) vs Windmills (a stretch)
    "row",  # two-arm barbell row vs one-arm dumbbell row: different movements
    "iron cross",  # three different exercises sharing a name
}

# Families by hand: {family name: [built-in exercise names]}.
MANUAL_GROUPS: dict[str, list[str]] = {
    # Bent-over rows with both arms at once (the one-arm rows stay separate).
    "Bent Over Row (two arms)": [
        "Barbell Row",
        "Bent Over Two-Dumbbell Row",
        "Two-Arm Kettlebell Row",
        "Smith Machine Bent Over Row",
    ],
}
