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
    # "preacher curl" is no longer doubtful: Preacher Curl uses a barbell since 2026-11-13.
    "decline press",
    "dip",  # 2026-11-06, with the parallel-bar dips below
    "deadlift",  # 2026-11-06, with the bar/machine versions below
    # 2026-11-14: Cable Lateral Raise is one-arm now (its source is a one-arm raise); the
    # owner kept it in the "Lateral Raise" family (MANUAL_GROUPS, 2026-11-13).
    "lateral raise",
}

REJECTED_GROUPS: set[str] = {
    "windmill",  # Kettlebell Windmill (strength) vs Windmills (a stretch)
    "row",  # two-arm barbell row vs one-arm dumbbell row: different movements
    "iron cross",  # three different exercises sharing a name
}

# Families by hand: {family name: [built-in exercise names]}.
MANUAL_GROUPS: dict[str, list[str]] = {
    # --- Reviewed by the owner on 2026-11-13 ("⇄ Change variant" shows the real exercise
    # instead of creating a copy). Same movement = same path and the same body position
    # (lying / seated / standing / bent over); a seated machine press is not a bench press.
    "Incline Bench Press": [
        "Incline Barbell Bench Press",
        "Smith Machine Incline Bench Press",
        "Incline Dumbbell Press",
    ],
    "Squat": ["Back Squat", "Smith Machine Squat", "Dumbbell Squat"],
    # 2026-11-15: Chair Squat is a Smith machine squat with the feet in front of the bar,
    # the same exercise as our Smith Machine Hack Squat (which now uses its photos).
    "Hack Squat": ["Hack Squat", "Barbell Hack Squat", "Smith Machine Hack Squat", "Chair Squat"],
    # 2026-11-14: the seated bent-over cable raise was the source of "Cable Lateral Raise";
    # same position and path as our Rear Delt Fly (Seated_Bent-Over_Rear_Delt_Raise).
    "Rear Delt Fly": ["Rear Delt Fly", "Cable Seated Lateral Raise"],
    "Chest Press": ["Machine Chest Press", "Leverage Chest Press"],
    "Fly": ["Dumbbell Fly", "Flat Bench Cable Flyes"],
    "Cable Crossover": ["Cable Crossover", "Cross Over - With Bands"],
    "Push-up": ["Push-up", "Suspended Push-Up"],
    "Pull-up": ["Pull-up", "Band Assisted Pull-Up", "Weighted Pull Ups"],
    "One-Arm Row": ["Dumbbell Row", "One-Arm Kettlebell Row"],
    "Seated Row": ["Seated Cable Row", "Leverage Iso Row"],
    "Overhead Press": [
        "Overhead Press",
        "Standing Dumbbell Press",
        "Two-Arm Kettlebell Military Press",
        "Shoulder Press - With Bands",
    ],
    # Two families that were the same seated press, plus the other seated machines.
    # Barbell Shoulder Press = Seated Barbell Military Press and Smith Machine Overhead
    # Shoulder Press = Smith Machine Seated Shoulder Press are duplicates (to be merged).
    "Seated Shoulder Press": [
        "Seated Dumbbell Shoulder Press",
        "Seated Barbell Military Press",
        "Seated Cable Shoulder Press",
        "Smith Machine Seated Shoulder Press",
        "Barbell Shoulder Press",
        "Machine Shoulder Press",
        "Cable Shoulder Press",
        "Leverage Shoulder Press",
        "Smith Machine Overhead Shoulder Press",
    ],
    "Lateral Raise": ["Lateral Raise", "Cable Lateral Raise", "Lateral Raise - With Bands"],
    "Shrug": ["Barbell Shrug", "Leverage Shrug"],
    "Hammer Curl": ["Hammer Curl", "Cable Hammer Curls - Rope Attachment"],
    "Preacher Curl": ["Preacher Curl", "Two-Arm Dumbbell Preacher Curl"],
    "Wrist Curl": ["Wrist Curl", "Seated Palm-Up Barbell Wrist Curl"],
    "Lying Triceps Extension": [
        "Skull Crusher",
        "Lying Dumbbell Tricep Extension",
        "Cable Lying Triceps Extension",
    ],
    "Overhead Triceps Extension": [
        "Overhead Cable Triceps Extension",
        "Overhead Dumbbell Triceps Extension",
        "Speed Band Overhead Triceps",
    ],
    "Front Squat": ["Front Squat", "Front Squats With Two Kettlebells"],
    # Smith Single-Leg Split Squat = Smith Machine Bulgarian Split Squat (to be merged).
    "Bulgarian Split Squat": [
        "Bulgarian Split Squat",
        "One Leg Barbell Squat",
        "Suspended Split Squat",
        "Smith Single-Leg Split Squat",
    ],
    "Walking Lunge": ["Walking Lunge", "Bodyweight Walking Lunge"],
    "Standing Calf Raise": [
        "Standing Calf Raise",
        "Smith Machine Calf Raise",
        "Calf Raises - With Bands",
    ],
    # Its instructions are a Romanian deadlift with dumbbells (see NOT_NAME_GROUPED).
    "Romanian Deadlift": ["Romanian Deadlift", "Stiff-Legged Dumbbell Deadlift"],
    # Single-leg deadlift: bodyweight (a balance exercise) and with a kettlebell (2026-11-13).
    "Single-Leg Deadlift": [
        "Kettlebell One-Legged Deadlift",
        "Bodyweight Single-Leg Romanian Deadlift",
    ],
    # Bent-over rows with both arms at once (the one-arm rows stay separate).
    "Bent Over Row (two arms)": [
        "Barbell Row",
        "Bent Over Two-Dumbbell Row",
        "Two-Arm Kettlebell Row",
        "Smith Machine Bent Over Row",
    ],
    # Dips on parallel bars (and the machine many people use); bench dips stay separate.
    "Dip": [
        "Dip",
        "Dip Machine",
        "Parallel Bar Dip",
        "Dips - Triceps Version",
        "Ring Dips",
    ],
    # The classic deadlift with other bars or a machine. Not: Romanian, sumo, stiff-legged,
    # or bands/chains (a way of loading, not a piece of equipment).
    "Deadlift": [
        "Deadlift",
        "Cable Deadlifts",
        "Smith Machine Deadlift",
        "Trap Bar Deadlift",
        "Axle Deadlift",
        "Leverage Deadlift",
    ],
}

# Built-ins kept out of the automatic grouping by name: their name puts them with one
# movement, their instructions with another (joined in MANUAL_GROUPS). Taken out of their
# old family on every run, so the two families never merge.
NOT_NAME_GROUPED: set[str] = {
    "Stiff-Legged Dumbbell Deadlift",  # an RDL with dumbbells, not a stiff-legged deadlift
}
