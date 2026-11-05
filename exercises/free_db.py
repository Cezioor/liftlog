"""Import of free-exercise-db (https://github.com/yuhonas/free-exercise-db, The Unlicense).

The dataset is stored in exercises/data/free_exercise_db.json, pinned to FREE_DB_COMMIT.
Images are not stored in the repo; they are served from jsDelivr at the same commit.

Rules (see CLAUDE.md, Stage 1.5):
- every imported exercise keeps a stable `source_id` (the dataset's "id"), so re-running
  the import updates rows instead of creating duplicates;
- the 65 original built-in exercises are never deleted or duplicated: LEGACY_MATCHES links
  each to its counterpart, which only *adds* data (muscles, images, instructions, level) and
  keeps the id, name, Polish names, muscle group, equipment and progression step;
- PENDING_MATCHES are originals with several plausible counterparts. Their candidates are
  not imported until the owner picks one, so confirming later can't create a duplicate.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction

from .free_db_polish import POLISH_NAMES
from .models import Equipment, Exercise, Muscle, MuscleGroup
from .services import default_progression_step

FREE_DB_COMMIT = "f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5"
IMAGE_BASE_URL = f"https://cdn.jsdelivr.net/gh/yuhonas/free-exercise-db@{FREE_DB_COMMIT}/exercises/"
DATA_FILE = Path(__file__).resolve().parent / "data" / "free_exercise_db.json"


def image_url(path):
    return IMAGE_BASE_URL + path


# --- mapping the dataset's vocabulary onto ours ---------------------------

MUSCLE_TO_GROUP = {
    Muscle.ABDOMINALS: MuscleGroup.CORE,
    # We have no separate hip group; hip abductors/adductors sit with the glutes.
    Muscle.ABDUCTORS: MuscleGroup.GLUTES,
    Muscle.ADDUCTORS: MuscleGroup.GLUTES,
    Muscle.BICEPS: MuscleGroup.BICEPS,
    Muscle.CALVES: MuscleGroup.CALVES,
    Muscle.CHEST: MuscleGroup.CHEST,
    Muscle.FOREARMS: MuscleGroup.FOREARMS,
    Muscle.GLUTES: MuscleGroup.GLUTES,
    Muscle.HAMSTRINGS: MuscleGroup.HAMSTRINGS,
    Muscle.LATS: MuscleGroup.BACK,
    Muscle.LOWER_BACK: MuscleGroup.BACK,
    Muscle.MIDDLE_BACK: MuscleGroup.BACK,
    Muscle.TRAPS: MuscleGroup.BACK,
    Muscle.NECK: MuscleGroup.OTHER,
    Muscle.QUADRICEPS: MuscleGroup.QUADS,
    Muscle.SHOULDERS: MuscleGroup.SHOULDERS,
    Muscle.TRICEPS: MuscleGroup.TRICEPS,
}

EQUIPMENT_MAP = {
    "barbell": Equipment.BARBELL,
    "e-z curl bar": Equipment.BARBELL,
    "dumbbell": Equipment.DUMBBELL,
    "machine": Equipment.MACHINE,
    "cable": Equipment.CABLE,
    "kettlebells": Equipment.KETTLEBELL,
    "bands": Equipment.BAND,
    "body only": Equipment.BODYWEIGHT,
    # foam roll, medicine ball, exercise ball, other, missing
}

LEVELS = {"beginner", "intermediate", "expert"}


def muscle_group_for(record):
    if record.get("category") == "olympic weightlifting":
        return MuscleGroup.FULL_BODY
    for muscle in record.get("primaryMuscles") or []:
        if muscle in MUSCLE_TO_GROUP:
            return MUSCLE_TO_GROUP[muscle]
    return MuscleGroup.OTHER


def equipment_for(record):
    return EQUIPMENT_MAP.get(record.get("equipment") or "", Equipment.OTHER)


def _known_muscles(names):
    return [m for m in (names or []) if m in Muscle.values]


def detail_fields(record):
    """Data copied from the dataset onto both new and matched original exercises."""
    return {
        "primary_muscles": _known_muscles(record.get("primaryMuscles")),
        "secondary_muscles": _known_muscles(record.get("secondaryMuscles")),
        "level": record.get("level") if record.get("level") in LEVELS else "",
        "category": record.get("category") or "",
        "mechanic": record.get("mechanic") or "",
        "instructions": [step.strip() for step in record.get("instructions") or [] if step.strip()],
        "images": list(record.get("images") or []),
        "source_name": record["name"].strip()[:120],
    }


# --- the 65 original exercises --------------------------------------------

# Reviewed by hand: original name -> free-exercise-db id.
LEGACY_MATCHES = {
    "Barbell Bench Press": "Barbell_Bench_Press_-_Medium_Grip",
    "Incline Barbell Bench Press": "Barbell_Incline_Bench_Press_-_Medium_Grip",
    "Dumbbell Bench Press": "Dumbbell_Bench_Press",
    "Incline Dumbbell Press": "Incline_Dumbbell_Press",
    "Dumbbell Fly": "Dumbbell_Flyes",
    "Cable Crossover": "Cable_Crossover",
    "Machine Chest Press": "Machine_Bench_Press",  # "Sit down on the Chest Press Machine"
    "Push-up": "Pushups",
    "Deadlift": "Barbell_Deadlift",
    "Barbell Row": "Bent_Over_Barbell_Row",
    "Dumbbell Row": "One-Arm_Dumbbell_Row",
    "Pull-up": "Pullups",
    "Chin-up": "Chin-Up",
    "Lat Pulldown": "Wide-Grip_Lat_Pulldown",
    "Seated Cable Row": "Seated_Cable_Rows",
    "Face Pull": "Face_Pull",
    "Back Extension": "Hyperextensions_Back_Extensions",
    "Overhead Press": "Standing_Military_Press",
    "Arnold Press": "Arnold_Dumbbell_Press",
    "Lateral Raise": "Side_Lateral_Raise",
    "Machine Shoulder Press": "Machine_Shoulder_Military_Press",
    "Barbell Shrug": "Barbell_Shrug",
    "Barbell Curl": "Barbell_Curl",
    "Dumbbell Curl": "Dumbbell_Bicep_Curl",
    "Hammer Curl": "Hammer_Curls",
    "Incline Dumbbell Curl": "Incline_Dumbbell_Curl",
    "Cable Curl": "Standing_Biceps_Cable_Curl",
    "Preacher Curl": "Preacher_Curl",
    "Close-Grip Bench Press": "Close-Grip_Barbell_Bench_Press",
    "Triceps Pushdown": "Triceps_Pushdown",
    "Overhead Cable Triceps Extension": "Cable_Rope_Overhead_Triceps_Extension",
    "Farmer's Walk": "Farmers_Walk",
    "Back Squat": "Barbell_Squat",
    "Front Squat": "Front_Barbell_Squat",
    "Leg Press": "Leg_Press",
    "Hack Squat": "Hack_Squat",
    "Leg Extension": "Leg_Extensions",
    "Bulgarian Split Squat": "Split_Squat_with_Dumbbells",  # rear foot elevated
    "Goblet Squat": "Goblet_Squat",
    "Romanian Deadlift": "Romanian_Deadlift",
    "Lying Leg Curl": "Lying_Leg_Curls",
    "Seated Leg Curl": "Seated_Leg_Curl",
    "Barbell Hip Thrust": "Barbell_Hip_Thrust",
    "Cable Pull-Through": "Pull_Through",
    "Standing Calf Raise": "Standing_Calf_Raises",
    "Seated Calf Raise": "Seated_Calf_Raise",
    "Plank": "Plank",
    "Hanging Leg Raise": "Hanging_Leg_Raise",
    "Cable Crunch": "Cable_Crunch",
    "Ab Wheel Rollout": "Ab_Roller",
    "Pallof Press": "Pallof_Press",
    "Power Clean": "Power_Clean",
    # Ambiguous ones, confirmed by the owner on 2026-11-05 (the other candidates are
    # imported as separate exercises).
    "Dip": "Dips_-_Chest_Version",
    "T-Bar Row": "Lying_T-Bar_Row",
    "Seated Dumbbell Shoulder Press": "Dumbbell_Shoulder_Press",
    "Cable Lateral Raise": "Cable_Seated_Lateral_Raise",
    "Rear Delt Fly": "Seated_Bent-Over_Rear_Delt_Raise",
    "Skull Crusher": "EZ-Bar_Skullcrusher",
    "Overhead Dumbbell Triceps Extension": "Standing_Dumbbell_Triceps_Extension",
    "Wrist Curl": "Seated_Dumbbell_Palms-Up_Wrist_Curl",
    "Walking Lunge": "Dumbbell_Lunges",
    "Nordic Hamstring Curl": "Natural_Glute_Ham_Raise",
    "Glute Bridge": "Butt_Lift_Bridge",
    "Kettlebell Swing": "One-Arm_Kettlebell_Swings",
}

# Originals with no counterpart in free-exercise-db; they stay exactly as they are.
UNMATCHED_ORIGINALS = {
    "Pendlay Row": "no counterpart; Bent_Over_Barbell_Row is already “Barbell Row”",
}

# Waiting for the owner's confirmation: original name -> candidate ids (proposal first).
# Candidates are NOT imported while listed here, so confirming later can't create a
# duplicate. To confirm, move the chosen id to LEGACY_MATCHES and re-run the import.
PENDING_MATCHES = {}


def withheld_ids():
    return {candidate for candidates in PENDING_MATCHES.values() for candidate in candidates}


# --- the import -----------------------------------------------------------


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    legacy_matched: list = field(default_factory=list)
    legacy_missing: list = field(default_factory=list)  # original not in the database
    withheld: int = 0
    conflicts: list = field(default_factory=list)  # (source_id, reason)


def load_dataset(path=DATA_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@transaction.atomic
def import_dataset(records):
    """Create or update built-in exercises from free-exercise-db records. Idempotent."""
    report = ImportReport()
    by_id = {record["id"]: record for record in records}
    legacy_ids = set(LEGACY_MATCHES.values())
    withheld = withheld_ids()

    # 1. Enrich the original exercises, keeping their id and our own fields.
    for name, source_id in LEGACY_MATCHES.items():
        record = by_id.get(source_id)
        exercise = Exercise.objects.filter(owner__isnull=True, name=name).first()
        if record is None or exercise is None:
            report.legacy_missing.append(name)
            continue
        taken = Exercise.objects.filter(source_id=source_id).exclude(pk=exercise.pk).first()
        if taken:
            report.conflicts.append((source_id, f"already used by “{taken.name}”"))
            continue
        for attr, value in detail_fields(record).items():
            setattr(exercise, attr, value)
        exercise.source_id = source_id
        exercise.save()
        report.legacy_matched.append(name)

    # 2. Everything else becomes (or updates) a built-in exercise keyed on source_id.
    builtin_names = {
        name.lower(): source_id
        for name, source_id in Exercise.objects.filter(owner__isnull=True).values_list(
            "name", "source_id"
        )
    }
    for record in records:
        source_id = record["id"]
        if source_id in legacy_ids:
            continue
        if source_id in withheld:
            report.withheld += 1
            continue
        name = record["name"].strip()[:100]
        holder = builtin_names.get(name.lower(), source_id)
        if holder != source_id:
            # Another built-in (e.g. an unmatched original) already has this name.
            report.conflicts.append((source_id, f"name “{name}” is taken"))
            continue

        muscle_group = muscle_group_for(record)
        equipment = equipment_for(record)
        _, created = Exercise.objects.update_or_create(
            source_id=source_id,
            defaults={
                "owner": None,
                "name": name,
                "aliases": POLISH_NAMES.get(source_id, ""),
                "muscle_group": muscle_group,
                "equipment": equipment,
                "is_bodyweight": equipment == Equipment.BODYWEIGHT,
                "progression_step_kg": default_progression_step(muscle_group, equipment),
                **detail_fields(record),
            },
        )
        builtin_names[name.lower()] = source_id
        if created:
            report.created += 1
        else:
            report.updated += 1
    return report
