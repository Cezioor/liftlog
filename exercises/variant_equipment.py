"""Equipment that "⇄ Change variant" offers for new variants of the popular movements.

Reviewed by the owner on 2026-11-13 (checked against all built-ins). Each list holds only
equipment for which a NEW variant would be created: the family's existing variants are
listed above it anyway, and equipment whose movement already exists as a separate
built-in (a seated machine press is not a bench press) is left out, so no copy of it is
made. Other equipment is not offered at all; "Other…" is always there.

A family is found by any of its built-in members' names. Families not listed here show
the equipment similar to what they already have (services.SIMILAR_EQUIPMENT).
"""

from .models import Equipment as E

SHOWN_EQUIPMENT = {
    # Chest
    "Barbell Bench Press": [],
    "Incline Barbell Bench Press": [],
    "Dumbbell Fly": [],
    "Cable Crossover": [],
    "Machine Chest Press": [],
    "Push-up": [E.BAND, E.PLATE],
    "Dip": [E.BAND],  # assisted
    # Back
    "Deadlift": [E.DUMBBELL, E.KETTLEBELL],
    "Barbell Row": [],
    "Pendlay Row": [],
    "Dumbbell Row": [E.CABLE, E.BAND],
    "Pull-up": [E.MACHINE],  # assisted
    "Chin-up": [E.BAND, E.MACHINE],  # assisted
    "Lat Pulldown": [E.MACHINE, E.BAND],
    "Seated Cable Row": [E.BAND],
    "T-Bar Row": [E.LANDMINE],
    "Face Pull": [E.BAND],
    "Back Extension": [E.PLATE],
    # Shoulders
    "Overhead Press": [E.SMITH, E.LANDMINE],  # standing
    "Seated Dumbbell Shoulder Press": [],
    "Arnold Press": [],
    "Lateral Raise": [E.MACHINE],
    "Rear Delt Fly": [],
    "Barbell Shrug": [E.KETTLEBELL],
    # Arms
    "Barbell Curl": [E.BAND],
    "Hammer Curl": [E.KETTLEBELL, E.BAND],
    "Incline Dumbbell Curl": [],
    "Preacher Curl": [],
    "Wrist Curl": [],
    "Farmer's Walk": [E.KETTLEBELL],
    "Close-Grip Bench Press": [E.DUMBBELL],
    "Skull Crusher": [],
    "Triceps Pushdown": [E.BAND],
    "Overhead Cable Triceps Extension": [],
    # Legs
    "Back Squat": [],
    "Front Squat": [],
    "Leg Press": [],
    "Hack Squat": [],
    "Leg Extension": [],
    "Bulgarian Split Squat": [E.KETTLEBELL, E.BODYWEIGHT],
    "Walking Lunge": [E.KETTLEBELL],
    "Goblet Squat": [],
    "Romanian Deadlift": [E.KETTLEBELL],
    "Lying Leg Curl": [],
    "Seated Leg Curl": [],
    "Nordic Hamstring Curl": [],
    "Barbell Hip Thrust": [E.MACHINE],
    "Glute Bridge": [E.DUMBBELL],
    "Cable Pull-Through": [E.BAND],
    "Standing Calf Raise": [E.BODYWEIGHT],
    "Seated Calf Raise": [E.DUMBBELL],
    # Core and full body
    "Plank": [E.PLATE],
    "Hanging Leg Raise": [],
    "Cable Crunch": [E.BAND],
    "Ab Wheel Rollout": [],
    "Pallof Press": [E.BAND],
    "Kettlebell Swing": [E.DUMBBELL],
    "Power Clean": [],
}
