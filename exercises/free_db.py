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
import re
from dataclasses import dataclass, field
from pathlib import Path

from django.db import transaction

from .free_db_polish import POLISH_NAMES
from .merges import merge_into
from .models import Category, Equipment, Exercise, Measurement, Muscle, MuscleGroup
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

CATEGORY_MAP = {
    "strength": Category.STRENGTH,
    "powerlifting": Category.STRENGTH,
    "olympic weightlifting": Category.STRENGTH,
    "strongman": Category.STRENGTH,
    "stretching": Category.MOBILITY,
    "plyometrics": Category.PLYOMETRIC,
    "cardio": Category.CARDIO,
}

# Cardio machines where the time matters more than the distance.
TIME_ONLY_CARDIO = {"Rope_Jumping", "Stairmaster", "Step_Mill", "Elliptical_Trainer"}
# Strongman events and sled work that are carried / pushed over a distance.
DISTANCE_WORDS = ("walk", "carry", "drag", "sled push", "prowler")
UNILATERAL_PATTERN = re.compile(
    r"\b(one[- ]arm|one[- ]leg|one[- ]legged|one[- ]handed|single[- ]arm|single[- ]leg)\b"
)


def type_fields(record):
    """measurement, category and is_unilateral for an imported exercise (Stage 1.6).

    Only used for exercises created by the import; the original 65 get theirs from
    seed_data.EXERCISE_TYPES and the import never overwrites them.
    """
    source_category = record.get("category") or ""
    name = record["name"].lower()
    static = record.get("force") == "static"

    if source_category == "stretching":
        measurement = Measurement.TIME
    elif source_category == "cardio":
        is_time_only = record["id"] in TIME_ONLY_CARDIO
        measurement = Measurement.TIME if is_time_only else Measurement.DISTANCE_TIME
    elif static:
        measurement = Measurement.TIME
    elif source_category == "strongman" and any(w in name for w in DISTANCE_WORDS):
        measurement = Measurement.DISTANCE_TIME
    elif source_category == "plyometrics" or record.get("equipment") == "body only":
        measurement = Measurement.REPS
    else:
        measurement = Measurement.WEIGHT_REPS

    category = CATEGORY_MAP.get(source_category, Category.STRENGTH)
    if static and category == Category.STRENGTH:
        category = Category.ISOMETRIC
    return {
        "measurement": measurement,
        "category": category,
        "is_unilateral": bool(UNILATERAL_PATTERN.search(name)),
    }


# Mistakes in the dataset, fixed on import (reviewed by the owner, 2026-11-13). The
# category feeds the "Type" filter and the library tiles. Measurements were changed only
# after checking that nobody had logged a set of these exercises.
SOURCE_CORRECTIONS = {
    "Isometric_Chest_Squeezes": {"category": Category.ISOMETRIC},  # was "plyometrics"
    "Balance_Board": {"category": Category.MOTOR, "measurement": Measurement.TIME},
    # Jumping lunges, filed under "stretching".
    "Split_Squats": {"category": Category.PLYOMETRIC, "measurement": Measurement.REPS},
    "Downward_Facing_Balance": {"category": Category.MOTOR},  # balancing on a ball
    "Superman": {"category": Category.ISOMETRIC},  # was "stretching"
    # Group "forearms", but the instructions describe rotating the shoulder.
    "Dumbbell_Lying_Supination": {"muscle_group": MuscleGroup.SHOULDERS},
    "Dumbbell_Lying_Pronation": {"muscle_group": MuscleGroup.SHOULDERS},
    # Joined to the families of their movement (2026-11-13); the dataset files them under
    # "other" and as weight × reps, unlike the rest of the family. Nobody had logged them.
    "Suspended_Push-Up": {"equipment": Equipment.SUSPENSION, "measurement": Measurement.REPS},
    "Band_Assisted_Pull-Up": {"equipment": Equipment.BAND, "measurement": Measurement.REPS},
    "Weighted_Pull_Ups": {"measurement": Measurement.REPS},  # kg stay: optional added weight
    "Bodyweight_Walking_Lunge": {
        "equipment": Equipment.BODYWEIGHT,
        "measurement": Measurement.REPS,
    },
    "Suspended_Split_Squat": {"equipment": Equipment.SUSPENSION},
}

# Our own instructions for originals whose free-exercise-db text doesn't fit them or is
# wrong (the Polish translation never differs from the English text, so mistakes are fixed
# here first), and for originals without a counterpart (set by seed_exercises). The photos
# stay: same movement, only the equipment or the number of hands differs, and the
# instructions say so.
ORIGINAL_INSTRUCTIONS = {
    # Source: hands "about 36 inches apart", far wider than a push-up.
    "Push-up": [
        "Lie on the floor face down and place your hands slightly wider than shoulder width "
        "apart while holding your torso up at arms length.",
        "Next, lower yourself downward until your chest almost touches the floor as you inhale.",
        "Now breathe out and press your upper body back up to the starting position while "
        "squeezing your chest.",
        "After a brief pause at the top contracted position, you can begin to lower yourself "
        "downward again for as many repetitions as needed.",
    ],
    # Source: "(my preference)" and an inhale on the way up as well as on the way down.
    "Back Extension": [
        "Lie face down on a hyperextension bench, tucking your ankles securely under the footpads.",
        "Adjust the upper pad if possible so your upper thighs lie flat across the wide pad, "
        "leaving enough room for you to bend at the waist without any restriction.",
        "With your body straight, cross your arms in front of you or behind your head. This "
        "will be your starting position. Tip: You can also hold a weight plate for extra "
        "resistance in front of you under your crossed arms.",
        "Start bending forward slowly at the waist as far as you can while keeping your back "
        "flat. Inhale as you perform this movement. Keep moving forward until you feel a nice "
        "stretch on the hamstrings and you can no longer keep going without a rounding of the "
        "back. Tip: Never round the back as you perform this exercise. Also, some people can "
        "go farther than others. The key thing is that you go as far as your body allows you "
        "to without rounding the back.",
        "Slowly raise your torso back to the initial position as you exhale. Tip: Avoid the "
        "temptation to arch your back past a straight line. Also, do not swing the torso at "
        "any time in order to protect the back from injury.",
        "Repeat for the recommended amount of repetitions.",
    ],
    # Source: "over your head" and "at about shoulder level" in one sentence.
    "Overhead Press": [
        "Start by placing a barbell that is about chest high on a squat rack. Once you have "
        "selected the weights, grab the barbell using a pronated (palms facing forward) grip. "
        "Make sure to grip the bar wider than shoulder width apart from each other.",
        "Slightly bend the knees and place the barbell on your collar bone. Lift the barbell "
        "up keeping it lying on your chest. Take a step back and position your feet shoulder "
        "width apart from each other.",
        "Once you pick up the barbell with the correct grip length, lift the bar up over your "
        "head by locking your arms. Hold it above your shoulders, slightly in front of your "
        "head. This is your starting position.",
        "Lower the bar down to the collarbone slowly as you inhale.",
        "Lift the bar back up to the starting position as you exhale.",
        "Repeat for the recommended amount of repetitions.",
    ],
    # Source: a note pointing to a missing foot stances section, and the old
    # "knees never past the toes" rule (now: heels down, knees in line with the toes).
    "Back Squat": [
        "This exercise is best performed inside a squat rack for safety purposes. To begin,"
        " first set the bar on a rack to just below shoulder level. Once the correct height"
        " is chosen and the bar is loaded, step under the bar and place the back of your "
        "shoulders (slightly below the neck) across it.",
        "Hold on to the bar using both arms at each side and lift it off the rack by first "
        "pushing with your legs and at the same time straightening your torso.",
        "Step away from the rack and position your legs using a shoulder width medium "
        "stance with the toes slightly pointed out. Keep your head up at all times and also"
        " maintain a straight back. This will be your starting position.",
        "Begin to slowly lower the bar by bending the knees and hips as you maintain a "
        "straight posture with the head up. Continue down until the angle between the upper"
        " leg and the calves becomes slightly less than 90-degrees. Inhale as you perform "
        "this portion of the movement. Tip: Keep your heels on the floor and your knees in "
        "line with your toes.",
        "Begin to raise the bar as you exhale by pushing the floor with the heel of your "
        "foot as you straighten the legs again and go back to the starting position.",
        "Repeat for the recommended amount of repetitions.",
    ],
    # Same as Back Squat.
    "Front Squat": [
        "This exercise is best performed inside a squat rack for safety purposes. To begin,"
        " first set the bar on a rack that best matches your height. Once the correct "
        "height is chosen and the bar is loaded, bring your arms up under the bar while "
        "keeping the elbows high and the upper arm slightly above parallel to the floor. "
        "Rest the bar on top of the deltoids and cross your arms while grasping the bar for"
        " total control.",
        "Lift the bar off the rack by first pushing with your legs and at the same time "
        "straightening your torso.",
        "Step away from the rack and position your legs using a shoulder width medium "
        "stance with the toes slightly pointed out. Keep your head up at all times as "
        "looking down will get you off balance and also maintain a straight back. This will"
        " be your starting position.",
        "Begin to slowly lower the bar by bending the knees as you maintain a straight "
        "posture with the head up. Continue down until the angle between the upper leg and "
        "the calves becomes slightly less than 90-degrees (which is the point in which the "
        "upper legs are below parallel to the floor). Inhale as you perform this portion of"
        " the movement. Tip: Keep your heels on the floor and your knees in line with your "
        "toes.",
        "Begin to raise the bar as you exhale by pushing the floor mainly with the middle "
        "of your foot as you straighten the legs again and go back to the starting "
        "position.",
        "Repeat for the recommended amount of repetitions.",
    ],
    # Same as Back Squat.
    "Hack Squat": [
        "Place the back of your torso against the back pad of the machine and hook your "
        "shoulders under the shoulder pads provided.",
        "Position your legs in the platform using a shoulder width medium stance with the "
        "toes slightly pointed out. Tip: Keep your head up at all times and also maintain "
        "the back on the pad at all times.",
        "Place your arms on the side handles of the machine and disengage the safety bars "
        "(which on most designs is done by moving the side handles from a facing front "
        "position to a diagonal position).",
        "Now straighten your legs without locking the knees. This will be your starting position.",
        "Begin to slowly lower the unit by bending the knees as you maintain a straight "
        "posture with the head up (back on the pad at all times). Continue down until the "
        "angle between the upper leg and the calves becomes slightly less than 90-degrees "
        "(which is the point in which the upper legs are below parallel to the floor). "
        "Inhale as you perform this portion of the movement. Tip: Keep your heels on the "
        "floor and your knees in line with your toes.",
        "Begin to raise the unit as you exhale by pushing the floor with mainly with the "
        "heel of your foot as you straighten the legs again and go back to the starting "
        "position.",
        "Repeat for the recommended amount of repetitions.",
    ],
    # Source: a note pointing to a missing foot positioning section.
    "Leg Press": [
        "Using a leg press machine, sit down on the machine and place your legs on the "
        "platform directly in front of you at a medium (shoulder width) foot stance.",
        "Lower the safety bars holding the weighted platform in place and press the "
        "platform all the way up until your legs are fully extended in front of you. Tip: "
        "Make sure that you do not lock your knees. Your torso and the legs should make a "
        "perfect 90-degree angle. This will be your starting position.",
        "As you inhale, slowly lower the platform until your upper and lower legs make a "
        "90-degree angle.",
        "Pushing mainly with the heels of your feet and using the quadriceps go back to the"
        " starting position as you exhale.",
        "Repeat for the recommended amount of repetitions and ensure to lock the safety "
        "pins properly once you are done. You do not want that platform falling on you "
        "fully loaded.",
    ],
    # Source: the old "knee over the toes" rationale and advice to look for another machine.
    "Leg Extension": [
        "For this exercise you will need to use a leg extension machine. First choose your "
        "weight and sit on the machine with your legs under the pad (feet pointed forward) "
        "and the hands holding the side bars. This will be your starting position. Tip: You"
        " will need to adjust the pad so that it falls on top of your lower leg (just above"
        " your feet). Also, make sure that your legs form a 90-degree angle between the "
        "lower and upper leg.",
        "Using your quadriceps, extend your legs to the maximum as you exhale. Ensure that "
        "the rest of the body remains stationary on the seat. Pause a second on the "
        "contracted position.",
        "Slowly lower the weight back to the original position as you inhale, ensuring that"
        " you do not go past the 90-degree angle limit.",
        "Repeat for the recommended amount of times.",
    ],
    # Source: notes pointing to a missing foot positioning section ("the beginning of the
    # chapter"), removed like in the squats.
    "Lying Leg Curl": [
        "Adjust the machine lever to fit your height and lie face down on the leg curl "
        "machine with the pad of the lever on the back of your legs (just a few inches "
        "under the calves). Tip: Preferably use a leg curl machine that is angled as "
        "opposed to flat since an angled position is more favorable for hamstrings "
        "recruitment.",
        "Keeping the torso flat on the bench, ensure your legs are fully stretched and grab"
        " the side handles of the machine. Position your toes straight. This will be your "
        "starting position.",
        "As you exhale, curl your legs up as far as possible without lifting the upper legs"
        " from the pad. Once you hit the fully contracted position, hold it for a second.",
        "As you inhale, bring the legs back to the initial position. Repeat for the "
        "recommended amount of repetitions.",
    ],
    "Seated Leg Curl": [
        "Adjust the machine lever to fit your height and sit on the machine with your back "
        "against the back support pad.",
        "Place the back of lower leg on top of padded lever (just a few inches under the "
        "calves) and secure the lap pad against your thighs, just above the knees. Then "
        "grasp the side handles on the machine as you point your toes straight and ensure "
        "that the legs are fully straight right in front of you. This will be your starting"
        " position.",
        "As you exhale, pull the machine lever as far as possible to the back of your "
        "thighs by flexing at the knees. Keep your torso stationary at all times. Hold the "
        "contracted position for a second.",
        "Slowly return to the starting position as you breathe in.",
        "Repeat for the recommended amount of repetitions.",
    ],
    "Standing Calf Raise": [
        "Adjust the padded lever of the calf raise machine to fit your height.",
        "Place your shoulders under the pads provided and position your toes facing "
        "forward. The balls of your feet should be secured on top of the calf block with "
        "the heels extending off it. Push the lever up by extending your hips and knees "
        "until your torso is standing erect. The knees should be kept with a slight bend; "
        "never locked. Toes should be facing forward, outwards or inwards. This will be "
        "your starting position.",
        "Raise your heels as you breathe out by extending your ankles as high as possible "
        "and flexing your calf. Ensure that the knee is kept stationary at all times. There"
        " should be no bending at any time. Hold the contracted position by a second before"
        " you start to go back down.",
        "Go back slowly to the starting position as you breathe in by lowering your heels "
        "as you bend the ankles until calves are stretched.",
        "Repeat for the recommended amount of repetitions.",
    ],
    "Seated Calf Raise": [
        "Sit on the machine and place your toes on the lower portion of the platform "
        "provided with the heels extending off. Choose the toe positioning of your choice "
        "(forward, in, or out).",
        "Place your lower thighs under the lever pad, which will need to be adjusted "
        "according to the height of your thighs. Now place your hands on top of the lever "
        "pad in order to prevent it from slipping forward.",
        "Lift the lever slightly by pushing your heels up and release the safety bar. This "
        "will be your starting position.",
        "Slowly lower your heels by bending at the ankles until the calves are fully "
        "stretched. Inhale as you perform this movement.",
        "Raise the heels by extending the ankles as high as possible as you contract the "
        "calves and breathe out. Hold the top contraction for a second.",
        "Repeat for the recommended amount of repetitions.",
    ],
    # Source: Cable Crunch let the weight hyperextend the lower back; Power Clean said
    # "inhale" right after "hold your breath" (owner, 2026-11-14).
    "Cable Crunch": [
        "Kneel below a high pulley that contains a rope attachment.",
        "Grasp cable rope attachment and lower the rope until your hands are placed next to"
        " your face.",
        "Flex your hips slightly and allow the weight to stretch your abs, keeping your "
        "lower back neutral. This will be your starting position.",
        "With the hips stationary, flex the waist as you contract the abs so that the "
        "elbows travel towards the middle of the thighs. Exhale as you perform this portion"
        " of the movement and hold the contraction for a second.",
        "Slowly return to the starting position as you inhale. Tip: Make sure that you keep"
        " constant tension on the abs throughout the movement. Also, do not choose a weight"
        " so heavy that the lower back handles the brunt of the work.",
        "Repeat for the recommended amount of repetitions.",
    ],
    "Power Clean": [
        "Stand with your feet slightly wider than shoulder width apart and toes pointing "
        "out slightly.",
        "Squat down and grasp bar with a closed, pronated grip. Your hands should be "
        "slightly wider than shoulder width apart outside knees with elbows fully extended.",
        "Place the bar about 1 inch in front of your shins and over the balls of your feet.",
        "Your back should be flat or slightly arched, your chest held up and out and your "
        "shoulder blades should be retracted.",
        "Keep your head in a neutral position (in line with vertebral column and not tilted"
        " or rotated) with your eyes focused straight ahead. Inhale during this phase.",
        "Lift the bar from the floor by forcefully extending the hips and the knees as you "
        "exhale. Tip: The upper torso should maintain the same angle. Do not bend at the "
        "waist yet and do not let the hips rise before the shoulders (this would have the "
        "effect of pushing the glutes in the air and stretching the hamstrings.",
        "Keep elbows fully extended with the head in a neutral position and the shoulders "
        "over the bar.",
        "As the bar raises keep it as close to the shins as possible.",
        "As the bar passes the knees, thrust your hips forward and slightly bend the knees "
        "to avoid locking them. Tip: At this point your thighs should be against the bar.",
        "Keep the back flat or slightly arched, elbows fully extended and your head "
        "neutral. Tip: You will hold your breath until the next phase.",
        "Forcefully and quickly extend your hips and knees and stand on your toes.",
        "Keep the bar as close to your body as possible. Tip: Your back should be flat with"
        " the elbows pointed out to the sides and your head in a neutral position. Also, "
        "keep your shoulders over the bar and arms straight as long as possible.",
        "When your lower body joints are fully extended, shrug the shoulders upward rapidly"
        " without letting the elbows flex yet. Exhale during this portion of the movement.",
        "As the shoulders reach their highest elevation flex your elbows to begin pulling "
        "your body under the bar.",
        "Continue to pull the arms as high and as long as possible. Tip: Due to the "
        "explosive nature of this phase, your torso will be erect or with an arched back, "
        "your head will be tilted back slightly and your feet may lose contact with the "
        "floor.",
        "After the lower body has fully extended and the bar reaches near maximal height, "
        "pull your body under the bar and rotate the arms around and under the bar.",
        "Simultaneously, flex the hips and knees into a quarter squat position.",
        "Once the arms are under the bar, inhale and then lift your elbows to position the "
        "upper arms parallel to the floor. Rack the bar across the front of your collar "
        "bones and front shoulder muscles.",
        "Catch the bar with an erect and tight torso, a neutral head position and flat "
        "feet. Exhale during this movement.",
        "Stand up by extending the hips and knees to a fully erect position.",
        "Lower the bar by gradually reducing the muscular tension of the arms to allow a "
        "controlled descent of the bar to the thighs. Inhale during this movement.",
        "Simultaneously flex the hips and knees to cushion the impact of the bar on the thighs.",
        "Squat down with the elbows fully extended until the bar touches the floor.",
        "Start over at Phase 1 and repeat for the recommended amount of repetitions.",
    ],
    # Its record (Dumbbell_Lunges) is a lunge in place (BORROWED_RECORDS); written by us.
    "Walking Lunge": [
        "Stand with your torso upright, holding a dumbbell in each hand by your sides. This "
        "will be your starting position.",
        "Step forward with one leg and lower your body until both knees are bent about 90 "
        "degrees and the back knee is just above the floor. Keep your torso upright. Inhale "
        "as you go down.",
        "As you exhale, push through the front heel and bring the back leg forward into the "
        "next step, so that you lunge with the other leg.",
        "Keep walking forward, alternating legs, for the recommended amount of repetitions.",
        "The photos show the same lunge done in place (Dumbbell Lunges).",
    ],
    # No counterpart in free-exercise-db (UNMATCHED_ORIGINALS); written by us.
    "Pendlay Row": [
        "Stand with your feet about hip width apart and the barbell on the floor over the "
        "middle of your feet. Hinge at the hips with a flat back until your torso is almost "
        "parallel to the floor, bend your knees slightly and grab the bar with an overhand "
        "grip a little wider than shoulder width. This will be your starting position.",
        "Keeping your back flat and your torso still, breathe out and pull the bar "
        "explosively to your lower chest, driving your elbows back.",
        "Breathe in and lower the bar under control back to the floor.",
        "Every repetition starts from a dead stop on the floor: do not bounce the bar or raise "
        "your torso. Repeat for the recommended amount of repetitions.",
    ],
    "Goblet Squat": [
        "Stand with your feet a little wider than shoulder width and hold one dumbbell "
        "vertically at your chest, both hands cupping the top end.",
        "Squat down between your legs, keeping your chest and head up and your back straight, "
        "until your thighs are at least parallel to the floor.",
        "At the bottom, use your elbows to push your knees out, then stand back up.",
        "The photos show the same squat with a kettlebell held by the horns (Kettlebell "
        "Goblet Squat).",
    ],
    "Kettlebell Swing": [
        "Stand with your feet a little wider than shoulder width, a kettlebell on the floor "
        "about a foot in front of you.",
        "Hinge at the hips with a flat back, grab the handle with both hands and hike the "
        "kettlebell back between your legs.",
        "Drive your hips forward explosively and stand tall: the kettlebell floats up to about "
        "chest height with straight arms. The power comes from the hips, not the arms.",
        "Let it swing back between your legs as you hinge again, and repeat.",
        "The photos show the one-arm version; the movement of the hips is the same.",
    ],
}


def muscle_group_for(record):
    if record.get("category") == "olympic weightlifting":
        return MuscleGroup.FULL_BODY
    for muscle in record.get("primaryMuscles") or []:
        if muscle in MUSCLE_TO_GROUP:
            return MUSCLE_TO_GROUP[muscle]
    return MuscleGroup.OTHER


def equipment_for(record):
    # free-exercise-db files Smith machine exercises under "machine" (one under
    # "barbell"); the name is the reliable sign.
    if "smith" in record.get("name", "").lower():
        return Equipment.SMITH
    return EQUIPMENT_MAP.get(record.get("equipment") or "", Equipment.OTHER)


def _known_muscles(names):
    return [m for m in (names or []) if m in Muscle.values]


def detail_fields(record):
    """Data copied from the dataset onto both new and matched original exercises."""
    return {
        "primary_muscles": _known_muscles(record.get("primaryMuscles")),
        "secondary_muscles": _known_muscles(record.get("secondaryMuscles")),
        "level": record.get("level") if record.get("level") in LEVELS else "",
        "source_category": record.get("category") or "",
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
    # Was Cable_Seated_Lateral_Raise (seated bent-over, rear delts) until 2026-11-14; that
    # one is now a built-in of its own (FOLDED_INTO_ORIGINALS).
    "Cable Lateral Raise": "Standing_Low-Pulley_Deltoid_Raise",
    "Rear Delt Fly": "Seated_Bent-Over_Rear_Delt_Raise",
    "Skull Crusher": "EZ-Bar_Skullcrusher",
    "Overhead Dumbbell Triceps Extension": "Standing_Dumbbell_Triceps_Extension",
    "Wrist Curl": "Seated_Dumbbell_Palms-Up_Wrist_Curl",
    "Walking Lunge": "Dumbbell_Lunges",  # photos and muscles only (BORROWED_RECORDS)
    "Nordic Hamstring Curl": "Natural_Glute_Ham_Raise",
    "Glute Bridge": "Butt_Lift_Bridge",
    "Kettlebell Swing": "One-Arm_Kettlebell_Swings",
}

# Built-ins folded into an original whose match moved to their source (owner, 2026-11-14):
# {source_id: original name}. Their sets, plan entries and swaps move to the original
# (merges.merge_into), the copy is deleted, then the original takes the source_id.
FOLDED_INTO_ORIGINALS = {"Standing_Low-Pulley_Deltoid_Raise": "Cable Lateral Raise"}

# Originals whose record is a similar but different exercise: it still gives them muscles
# and photos (their own text is in ORIGINAL_INSTRUCTIONS), but its source_id stays free,
# so the record is also imported as a built-in of its own. Walking Lunge: Dumbbell_Lunges
# is a lunge in place, now the built-in "Dumbbell Lunges" (owner, 2026-11-14).
BORROWED_RECORDS = {"Walking Lunge"}

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
    folded: list = field(default_factory=list)  # merges.MergeResult


def load_dataset(path=DATA_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@transaction.atomic
def import_dataset(records):
    """Create or update built-in exercises from free-exercise-db records. Idempotent."""
    report = ImportReport()
    by_id = {record["id"]: record for record in records}
    legacy_ids = {sid for name, sid in LEGACY_MATCHES.items() if name not in BORROWED_RECORDS}
    withheld = withheld_ids()

    # 0. A built-in holding a source an original moves to is folded into that original.
    for source_id, name in FOLDED_INTO_ORIGINALS.items():
        original = Exercise.objects.filter(owner__isnull=True, name=name).first()
        holder = Exercise.objects.filter(owner__isnull=True, source_id=source_id)
        holder = holder.exclude(pk=original.pk).first() if original else None
        if holder:
            report.folded.append(merge_into(holder, original))

    # 1. Enrich the original exercises, keeping their id and our own fields.
    for name, source_id in LEGACY_MATCHES.items():
        record = by_id.get(source_id)
        exercise = Exercise.objects.filter(owner__isnull=True, name=name).first()
        if record is None or exercise is None:
            report.legacy_missing.append(name)
            continue
        borrowed = name in BORROWED_RECORDS
        taken = Exercise.objects.filter(source_id=source_id).exclude(pk=exercise.pk).first()
        if taken and not borrowed:
            report.conflicts.append((source_id, f"already used by “{taken.name}”"))
            continue
        for attr, value in detail_fields(record).items():
            setattr(exercise, attr, value)
        if name in ORIGINAL_INSTRUCTIONS:
            exercise.instructions = ORIGINAL_INSTRUCTIONS[name]
        exercise.source_id = None if borrowed else source_id
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

        corrections = SOURCE_CORRECTIONS.get(source_id, {})
        muscle_group = corrections.get("muscle_group", muscle_group_for(record))
        equipment = corrections.get("equipment", equipment_for(record))
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
                **type_fields(record),
                **corrections,
            },
        )
        builtin_names[name.lower()] = source_id
        if created:
            report.created += 1
        else:
            report.updated += 1
    return report
