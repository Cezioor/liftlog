"""Built-in exercise library loaded by `python manage.py seed_exercises`.

Each tuple: (name, muscle_group, equipment, is_bodyweight).
"""

from decimal import Decimal

from .holds_balance import HOLDS_AND_BALANCE

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
    # The instructions use an E-Z bar on a preacher bench (was "machine" until 2026-11-13).
    ("Preacher Curl", "biceps", "barbell", False),
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

# Polish names and synonyms (comma separated). Search ignores case and diacritics.
ALIASES = {
    # Chest
    "Barbell Bench Press": "wyciskanie sztangi na ławce płaskiej, wyciskanie na ławce płaskiej, "
    "wyciskanie sztangi leżąc, ławka płaska",
    "Incline Barbell Bench Press": "wyciskanie sztangi na ławce skośnej, "
    "wyciskanie na skosie dodatnim, ławka skośna",
    "Dumbbell Bench Press": "wyciskanie hantli na ławce płaskiej, wyciskanie hantli leżąc",
    "Incline Dumbbell Press": "wyciskanie hantli na ławce skośnej, wyciskanie hantli skos",
    "Dumbbell Fly": "rozpiętki z hantlami, rozpiętki na ławce",
    "Cable Crossover": "rozpiętki na wyciągu, krzyżowanie linek wyciągu, brama",
    "Machine Chest Press": "wyciskanie na maszynie, maszyna do klatki",
    "Push-up": "pompki",
    "Dip": "pompki na poręczach, dipy",
    # Back
    "Deadlift": "martwy ciąg, martwy ciąg klasyczny",
    "Barbell Row": "wiosłowanie sztangą, wiosłowanie sztangą w opadzie tułowia",
    "Pendlay Row": "wiosłowanie pendlay, wiosłowanie sztangą z podłogi",
    "Dumbbell Row": "wiosłowanie hantlem, wiosłowanie hantlem jednorącz",
    "Pull-up": "podciąganie na drążku, podciąganie nachwytem",
    "Chin-up": "podciąganie podchwytem, podciąganie na drążku podchwytem",
    "Lat Pulldown": "ściąganie drążka wyciągu górnego, ściąganie drążka do klatki, wyciąg górny",
    "Seated Cable Row": "wiosłowanie na wyciągu siedząc, przyciąganie linki wyciągu dolnego, "
    "wyciąg dolny",
    "T-Bar Row": "wiosłowanie t-bar, wiosłowanie na maszynie",
    "Face Pull": "przyciąganie liny do twarzy",
    "Back Extension": "wyprosty tułowia, prostowniki grzbietu, ławka rzymska",
    # Shoulders
    "Overhead Press": "wyciskanie żołnierskie, wyciskanie sztangi nad głowę, ohp",
    "Seated Dumbbell Shoulder Press": "wyciskanie hantli nad głowę siedząc, "
    "wyciskanie hantli na barki",
    "Arnold Press": "arnoldki, wyciskanie arnolda",
    "Lateral Raise": "wznosy bokiem z hantlami, unoszenie ramion bokiem",
    "Cable Lateral Raise": "wznosy bokiem na wyciągu, unoszenie ramienia bokiem na wyciągu, "
    "wznosy bokiem jednorącz na dolnym wyciągu, wznosy bokiem na wyciągu jedną ręką, "
    "boczne barki na wyciągu",
    "Rear Delt Fly": "odwrotne rozpiętki, wznosy w opadzie, tylny akton barków",
    "Machine Shoulder Press": "wyciskanie nad głowę na maszynie, maszyna na barki",
    "Barbell Shrug": "szrugsy, wzruszanie ramion ze sztangą, kaptury",
    # Biceps
    "Barbell Curl": "uginanie ramion ze sztangą, zgięcia ramion ze sztangą, biceps sztangą",
    "Dumbbell Curl": "uginanie ramion z hantlami, zgięcia ramion z hantlami, biceps hantlami",
    "Hammer Curl": "uginanie młotkowe, młotki, zgięcia młotkowe",
    "Incline Dumbbell Curl": "uginanie ramion na ławce skośnej, zgięcia ramion na skosie",
    "Cable Curl": "uginanie ramion na wyciągu, zgięcia ramion na wyciągu",
    "Preacher Curl": "uginanie na modlitewniku, modlitewnik, zgięcia na modlitewniku",
    # Triceps
    "Close-Grip Bench Press": "wyciskanie wąskim chwytem, wyciskanie sztangi wąsko",
    "Skull Crusher": "wyciskanie francuskie leżąc, francuz leżąc",
    "Triceps Pushdown": "prostowanie ramion na wyciągu górnym, prostowanie przedramion na wyciągu",
    "Overhead Cable Triceps Extension": "prostowanie ramion nad głową na wyciągu, "
    "francuz na wyciągu",
    "Overhead Dumbbell Triceps Extension": "wyciskanie francuskie hantlem, "
    "prostowanie ramion nad głową z hantlem, francuz hantlem",
    # Forearms
    "Wrist Curl": "uginanie nadgarstków, zgięcia nadgarstków, przedramiona",
    "Farmer's Walk": "spacer farmera, chód farmera",
    # Quads
    "Back Squat": "przysiad ze sztangą, przysiad ze sztangą na plecach, przysiady",
    "Front Squat": "przysiad przedni, przysiad ze sztangą z przodu",
    "Leg Press": "wypychanie nogami na suwnicy, suwnica, prasa nożna",
    "Hack Squat": "przysiad hack, przysiad na maszynie",
    "Leg Extension": "prostowanie nóg na maszynie, wyprosty nóg siedząc",
    "Bulgarian Split Squat": "przysiad bułgarski, bułgary",
    # "wykroki z hantlami" moved to Dumbbell Lunges (a lunge in place) on 2026-11-14.
    "Walking Lunge": "wykroki chodzone, wykroki chodzone z hantlami",
    "Goblet Squat": "przysiad goblet, przysiad z hantlem",
    # Hamstrings
    "Romanian Deadlift": "martwy ciąg rumuński, rdl",
    "Lying Leg Curl": "uginanie nóg leżąc, zgięcia nóg leżąc, dwugłowe uda",
    "Seated Leg Curl": "uginanie nóg siedząc, zgięcia nóg siedząc",
    "Nordic Hamstring Curl": "uginanie nordyckie, nordic curl",
    # Glutes
    "Barbell Hip Thrust": "wypychanie bioder ze sztangą, hip thrust, pośladki",
    "Glute Bridge": "mostek biodrowy, unoszenie bioder leżąc",
    "Cable Pull-Through": "przeciąganie linki między nogami, pull through",
    # Calves
    "Standing Calf Raise": "wspięcia na palce stojąc, łydki stojąc",
    "Seated Calf Raise": "wspięcia na palce siedząc, łydki siedząc",
    # Core
    "Plank": "deska, podpór przodem",
    "Hanging Leg Raise": "unoszenie nóg w zwisie, wznosy nóg w zwisie",
    "Cable Crunch": "spięcia brzucha na wyciągu, allahy, brzuszki na wyciągu",
    "Ab Wheel Rollout": "kółko do brzucha, roller do brzucha",
    "Pallof Press": "wyciskanie pallofa, antyrotacja",
    # Full body
    "Kettlebell Swing": "swing kettlebell, wymachy kettlebell",
    "Power Clean": "zarzut siłowy, zarzut",
}

# Stage 1.6: how the original exercises are logged. Anything not listed is
# ("weight_reps", "strength", False). Old sets keep their weight × reps either way.
EXERCISE_TYPES = {
    # name: (measurement, category, is_unilateral)
    "Push-up": ("reps", "strength", False),
    "Dip": ("reps", "strength", False),
    "Pull-up": ("reps", "strength", False),
    "Chin-up": ("reps", "strength", False),
    "Back Extension": ("reps", "strength", False),
    "Nordic Hamstring Curl": ("reps", "strength", False),
    "Glute Bridge": ("reps", "strength", False),
    "Hanging Leg Raise": ("reps", "strength", False),
    "Ab Wheel Rollout": ("reps", "strength", False),
    "Plank": ("time", "isometric", False),
    "Farmer's Walk": ("distance_time", "strength", False),
    "Dumbbell Row": ("weight_reps", "strength", True),
    "Bulgarian Split Squat": ("weight_reps", "strength", True),
    # One arm at a time since its source is Standing_Low-Pulley_Deltoid_Raise (2026-11-14).
    "Cable Lateral Raise": ("weight_reps", "strength", True),
}

# Built-in exercises that free-exercise-db lacks: isometric holds, balance, rehab basics.
# Each: name, muscle_group, equipment, measurement, category, is_unilateral,
#       primary muscles, secondary muscles, Polish names, instructions.
EXTRA_EXERCISES = [
    {
        "name": "Spanish Squat Hold",
        "muscle_group": "quads",
        "equipment": "band",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": ["quadriceps"],
        "secondary_muscles": ["glutes"],
        "aliases": "przysiad hiszpański, izometria przysiadu z gumą, spanish squat",
        "instructions": [
            "Loop a heavy band around a rack at knee height and step into it so it sits "
            "behind your knees.",
            "Lean back against the band and sit down until your shins are vertical and "
            "your knees are bent about 60–90°.",
            "Keep your chest up and hold the position, breathing normally.",
        ],
    },
    {
        "name": "Copenhagen Plank",
        "muscle_group": "glutes",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": True,
        "level": "intermediate",
        "primary_muscles": ["adductors"],
        "secondary_muscles": ["abdominals"],
        "aliases": "deska kopenhaska, plank kopenhaski, przywodziciele",
        "instructions": [
            "Lie on your side next to a bench and place your top leg on it "
            "(knee for the easier version, ankle for the harder one).",
            "Lift your hips so your body forms a straight line, supported on your forearm "
            "and the top leg.",
            "Hold, then switch sides.",
        ],
    },
    {
        "name": "Single-Leg Balance",
        "muscle_group": "calves",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "motor",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": ["calves"],
        "secondary_muscles": ["glutes", "abdominals"],
        "aliases": "stanie na jednej nodze, równowaga na jednej nodze, balans",
        "instructions": [
            "Stand on one leg with a slightly bent knee, near a wall or rack for safety.",
            "Keep your hips level and your eyes on a fixed point.",
            "Hold, then switch legs. Close your eyes or stand on a balance pad to make it harder.",
        ],
    },
    {
        "name": "Wall Sit",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": ["quadriceps"],
        "secondary_muscles": ["glutes"],
        "aliases": "krzesełko, siad przy ścianie, wall sit",
        "instructions": [
            "Lean your back against a wall and slide down until your thighs are about "
            "parallel to the floor.",
            "Keep your knees above your ankles and your back flat on the wall.",
            "Hold the position.",
        ],
    },
    {
        "name": "Dead Hang",
        "muscle_group": "forearms",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": ["forearms"],
        "secondary_muscles": ["lats", "shoulders"],
        "aliases": "zwis na drążku, zwis",
        "instructions": [
            "Grab a pull-up bar with a shoulder-width overhand grip.",
            "Hang with straight arms and relaxed legs.",
            "Hold as long as you can keep a firm grip.",
        ],
    },
    {
        "name": "Hollow Body Hold",
        "muscle_group": "core",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": ["abdominals"],
        "secondary_muscles": [],
        "aliases": "łódka, hollow hold, trzymanie łódki",
        "instructions": [
            "Lie on your back, press your lower back into the floor.",
            "Lift your shoulders and legs a few centimetres off the floor, arms by your ears.",
            "Hold without letting your lower back lift. Bend your knees to make it easier.",
        ],
    },
]

# Isometric holds and balance exercises (reviewed by the owner, 2026-11-13).
EXTRA_EXERCISES += HOLDS_AND_BALANCE

# free-exercise-db's goblet squat uses a kettlebell (its text and photos), while our
# original Goblet Squat is the dumbbell one: the kettlebell version is its own variant.
EXTRA_EXERCISES.append(
    {
        "name": "Kettlebell Goblet Squat",
        "muscle_group": "quads",
        "equipment": "kettlebell",
        "measurement": "weight_reps",
        "category": "strength",
        "is_unilateral": False,
        "level": "beginner",
        "mechanic": "compound",
        "primary_muscles": ["quadriceps"],
        "secondary_muscles": ["calves", "glutes", "hamstrings", "shoulders"],
        "aliases": "przysiad goblet z kettlebell, goblet squat kettlebell, przysiad z kettlebell",
        "images": ["Goblet_Squat/0.jpg", "Goblet_Squat/1.jpg"],
        "instructions": [
            "Stand holding a light kettlebell by the horns close to your chest. This will be "
            "your starting position.",
            "Squat down between your legs until your hamstrings are on your calves. Keep your "
            "chest and head up and your back straight.",
            "At the bottom position, pause and use your elbows to push your knees out. Return "
            "to the starting position, and repeat for the recommended amount of repetitions.",
        ],
    }
)

# Levels for originals that free-exercise-db has no counterpart for (the import sets the
# others' level from their match).
ORIGINAL_LEVELS = {"Pendlay Row": "intermediate"}

# Notes shown under the photos of originals whose photos are not exactly the exercise
# (same movement, other equipment or number of hands): name -> (English, Polish).
PHOTO_NOTES = {
    "Goblet Squat": (
        "The photos show the same squat with a kettlebell held by the horns "
        "(Kettlebell Goblet Squat).",
        "Zdjęcia pokazują ten sam przysiad z kettlebell trzymanym za rogi "
        "(przysiad goblet z kettlebell).",
    ),
    "Kettlebell Swing": (
        "The photos show the one-arm version; the movement of the hips is the same.",
        "Zdjęcia pokazują wersję jednorącz; praca bioder jest taka sama.",
    ),
    "Walking Lunge": (
        "The photos show the same lunge done in place (Dumbbell Lunges).",
        "Zdjęcia pokazują ten sam wykrok wykonywany w miejscu (wykroki z hantlami).",
    ),
}
