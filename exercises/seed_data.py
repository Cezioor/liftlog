"""Built-in exercise library loaded by `python manage.py seed_exercises`.

Each tuple: (name, muscle_group, equipment, is_bodyweight).
"""

from decimal import Decimal

EXERCISES = [
    # Chest
    ("Barbell Bench Press", "chest", "barbell", False),
    ("Incline Barbell Bench Press", "chest", "barbell", False),
    ("Dumbbell Bench Press", "chest", "dumbbell", False),
    ("Incline Dumbbell Press", "chest", "dumbbell", False),
    ("Dumbbell Fly", "chest", "dumbbell", False),
    ("Cable Crossover", "chest", "cable", False),
    ("Machine Chest Press", "chest", "machine", False),
    ("Push-up", "chest", "bodyweight", True),
    ("Dip", "chest", "bodyweight", True),
    # Back
    ("Deadlift", "back", "barbell", False),
    ("Barbell Row", "back", "barbell", False),
    ("Pendlay Row", "back", "barbell", False),
    ("Dumbbell Row", "back", "dumbbell", False),
    ("Pull-up", "back", "bodyweight", True),
    ("Chin-up", "back", "bodyweight", True),
    ("Lat Pulldown", "back", "cable", False),
    ("Seated Cable Row", "back", "cable", False),
    ("T-Bar Row", "back", "machine", False),
    ("Face Pull", "back", "cable", False),
    ("Back Extension", "back", "bodyweight", True),
    # Shoulders
    ("Overhead Press", "shoulders", "barbell", False),
    ("Seated Dumbbell Shoulder Press", "shoulders", "dumbbell", False),
    ("Arnold Press", "shoulders", "dumbbell", False),
    ("Lateral Raise", "shoulders", "dumbbell", False),
    ("Cable Lateral Raise", "shoulders", "cable", False),
    ("Rear Delt Fly", "shoulders", "dumbbell", False),
    ("Machine Shoulder Press", "shoulders", "machine", False),
    ("Barbell Shrug", "shoulders", "barbell", False),
    # Biceps
    ("Barbell Curl", "biceps", "barbell", False),
    ("Dumbbell Curl", "biceps", "dumbbell", False),
    ("Hammer Curl", "biceps", "dumbbell", False),
    ("Incline Dumbbell Curl", "biceps", "dumbbell", False),
    ("Cable Curl", "biceps", "cable", False),
    ("Preacher Curl", "biceps", "machine", False),
    # Triceps
    ("Close-Grip Bench Press", "triceps", "barbell", False),
    ("Skull Crusher", "triceps", "barbell", False),
    ("Triceps Pushdown", "triceps", "cable", False),
    ("Overhead Cable Triceps Extension", "triceps", "cable", False),
    ("Overhead Dumbbell Triceps Extension", "triceps", "dumbbell", False),
    # Forearms
    ("Wrist Curl", "forearms", "dumbbell", False),
    ("Farmer's Walk", "forearms", "dumbbell", False),
    # Quads
    ("Back Squat", "quads", "barbell", False),
    ("Front Squat", "quads", "barbell", False),
    ("Leg Press", "quads", "machine", False),
    ("Hack Squat", "quads", "machine", False),
    ("Leg Extension", "quads", "machine", False),
    ("Bulgarian Split Squat", "quads", "dumbbell", False),
    ("Walking Lunge", "quads", "dumbbell", False),
    ("Goblet Squat", "quads", "dumbbell", False),
    # Hamstrings
    ("Romanian Deadlift", "hamstrings", "barbell", False),
    ("Lying Leg Curl", "hamstrings", "machine", False),
    ("Seated Leg Curl", "hamstrings", "machine", False),
    ("Nordic Hamstring Curl", "hamstrings", "bodyweight", True),
    # Glutes
    ("Barbell Hip Thrust", "glutes", "barbell", False),
    ("Glute Bridge", "glutes", "bodyweight", True),
    ("Cable Pull-Through", "glutes", "cable", False),
    # Calves
    ("Standing Calf Raise", "calves", "machine", False),
    ("Seated Calf Raise", "calves", "machine", False),
    # Core
    ("Plank", "core", "bodyweight", True),
    ("Hanging Leg Raise", "core", "bodyweight", True),
    ("Cable Crunch", "core", "cable", False),
    ("Ab Wheel Rollout", "core", "other", True),
    ("Pallof Press", "core", "cable", False),
    # Full body
    ("Kettlebell Swing", "full_body", "kettlebell", False),
    ("Power Clean", "full_body", "barbell", False),
]

# Exceptions to exercises.services.default_progression_step.
PROGRESSION_STEP_OVERRIDES = {
    # Listed under "back", but it is loaded and progressed like a leg lift.
    "Deadlift": Decimal("5"),
}
