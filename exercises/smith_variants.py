"""Built-in Smith machine variants that free-exercise-db doesn't have.

Each one names the free-weight exercise it comes from: `group_movements` puts the two in
one movement family, and the variant borrows the base's photos. Seeded by the
`seed_smith_variants` command, which build.sh runs after the free-exercise-db import
(the bases come from that import).

Fields: name, base exercise name (None if the library has no close match), Polish names,
muscle group, main muscles, helping muscles, measurement, one side at a time, steps.
"""

# Levels of the variants without a base exercise (the others take the base's level).
BASELESS_LEVELS = {
    "Smith Machine Curtsy Lunge": "beginner",
    "Smith Machine Reverse-Grip Bench Press": "beginner",
    "Smith Machine Sumo Squat": "beginner",
}

# free-exercise-db records that are one of these variants under another name:
# {variant name: source_id}. The import skips them; `seed_smith_variants` folds a built-in
# copy left by older imports into the variant (merges.merge_into: sets, plan entries,
# swaps) and gives the variant the record's photos, with no note (same exercise; they still
# share the base's family, level and mechanic). Barbell Hack Squat holds the bar behind the
# legs; on the Smith machine the bar is on the back with the feet in front of it, which is
# what free-exercise-db's "Chair Squat" is (owner, 2026-11-15: one exercise, not two).
ABSORBED_SOURCES = {"Smith Machine Hack Squat": "Chair_Squat"}

# Under the photos of variants whose base is done with free weights (English, Polish);
# bases with other equipment (a machine, bodyweight) get the second note.
FREE_WEIGHT_PHOTO_NOTE = (
    "The photos show the same movement with free weights.",
    "Zdjęcia pokazują ten sam ruch z wolnym ciężarem.",
)
OTHER_BASE_PHOTO_NOTE = (
    "The photos show the same movement without a Smith machine.",
    "Zdjęcia pokazują ten sam ruch bez suwnicy Smitha.",
)
FREE_WEIGHTS = {"barbell", "dumbbell", "kettlebell"}

# Shared first step: the Smith bar runs on rails, so setting the hooks matters most.
SET_BAR = "Set the bar height and the safety stops before you load the bar."

SMITH_VARIANTS = [
    # --- legs and glutes ---------------------------------------------------------
    (
        "Smith Machine Step-up",
        "Barbell Step Ups",
        (
            "wejścia na skrzynię na smithie, wejścia na skrzynię na suwnicy smitha, "
            "wejście na podest smith, step up smith"
        ),
        "quads",
        ["quadriceps", "glutes"],
        ["hamstrings"],
        "weight_reps",
        True,
        [
            SET_BAR,
            "Put a box under the bar, the bar on your upper back, one foot on the box.",
            "Drive through the front heel until you stand on the box; step down with control.",
        ],
    ),
    (
        "Smith Machine Lunge",
        "Barbell Lunge",
        "wykroki na smithie, wykroki na suwnicy smitha, wykrok w miejscu smith, lunge smith",
        "quads",
        ["quadriceps", "glutes"],
        ["hamstrings"],
        "weight_reps",
        True,
        [
            SET_BAR,
            "Stand in a long split stance under the bar, bar on your upper back.",
            "Lower straight down until the back knee nearly touches the floor, then push up.",
        ],
    ),
    (
        "Smith Machine Reverse Lunge",
        "Dumbbell Rear Lunge",
        (
            "wykroki w tył na smithie, wykroki w tył na suwnicy smitha, zakroki smith, "
            "reverse lunge smith"
        ),
        "glutes",
        ["glutes", "quadriceps"],
        ["hamstrings"],
        "weight_reps",
        True,
        [
            SET_BAR,
            "Stand under the bar with feet together, bar on your upper back.",
            "Step one foot back and lower until the back knee nearly touches the floor.",
            "Push through the front foot to return; finish all reps on one side.",
        ],
    ),
    (
        "Smith Machine Curtsy Lunge",
        None,
        (
            "wykroki skrzyżne na smithie, wykroki skrzyżne na suwnicy smitha, curtsy lunge smith, "
            "wykrok dygnięcie"
        ),
        "glutes",
        ["glutes"],
        ["quadriceps", "abductors"],
        "weight_reps",
        True,
        [
            SET_BAR,
            "Stand under the bar, bar on your upper back.",
            "Step one leg back and across behind the other, lower until the front thigh is "
            "about parallel, then return.",
        ],
    ),
    (
        "Smith Machine Bulgarian Split Squat",
        "Bulgarian Split Squat",
        (
            "przysiad bułgarski na smithie, przysiad bułgarski na suwnicy smitha, "
            "bułgarski przysiad na smithie, "
            "przysiad bułgarski smith, bulgarian smith"
        ),
        "quads",
        ["quadriceps", "glutes"],
        ["hamstrings"],
        "weight_reps",
        True,
        [
            SET_BAR,
            "Bar on your upper back, rear foot on a bench behind you.",
            "Lower straight down until the front thigh is about parallel, then drive up.",
        ],
    ),
    (
        "Smith Machine Hip Thrust",
        "Barbell Hip Thrust",
        (
            "hip thrust na smithie, hip thrust na suwnicy smitha, wypychanie bioder smith, "
            "unoszenie bioder smith"
        ),
        "glutes",
        ["glutes"],
        ["hamstrings"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Sit with your upper back against a bench, bar padded across your hips.",
            "Drive your hips up until your body is straight from knees to shoulders.",
            "Squeeze the glutes at the top, lower with control.",
        ],
    ),
    (
        "Smith Machine Single-Leg Hip Thrust",
        "Barbell Hip Thrust",
        (
            "hip thrust jednonóż na smithie, hip thrust jednonóż na suwnicy smitha, "
            "unoszenie bioder na jednej nodze smith"
        ),
        "glutes",
        ["glutes"],
        ["hamstrings"],
        "weight_reps",
        True,
        [
            SET_BAR,
            "Set up as for a hip thrust, then lift one foot off the floor.",
            "Drive up through the planted heel, keep the hips level, lower with control.",
        ],
    ),
    (
        "Smith Machine Glute Bridge",
        "Barbell Glute Bridge",
        "mostek biodrowy na smithie, mostek biodrowy na suwnicy smitha, glute bridge smith",
        "glutes",
        ["glutes"],
        ["hamstrings"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Lie on the floor, knees bent, the padded bar across your hips.",
            "Push your hips up until your body is straight from knees to shoulders, then lower.",
        ],
    ),
    (
        "Smith Machine Romanian Deadlift",
        "Romanian Deadlift",
        (
            "martwy ciąg rumuński na smithie, martwy ciąg rumuński na suwnicy smitha, rdl smith, "
            "rumuński smith"
        ),
        "hamstrings",
        ["hamstrings"],
        ["glutes", "lower back"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Hold the bar at hip height, feet under the bar, knees soft.",
            "Push your hips back and lower the bar along your legs with a flat back.",
            "Stop when you feel the hamstrings stretch, then drive the hips forward.",
        ],
    ),
    (
        "Smith Machine Deadlift",
        "Deadlift",
        "martwy ciąg na smithie, martwy ciąg na suwnicy smitha, deadlift smith",
        "hamstrings",
        ["lower back", "glutes"],
        ["hamstrings", "quadriceps", "traps"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Feet under the bar, grip just outside the knees, flat back.",
            "Stand up by pushing the floor away; lower the same way.",
        ],
    ),
    (
        "Smith Machine Rack Pull",
        "Rack Pulls",
        (
            "martwy ciąg ze stojaków na smithie, martwy ciąg ze stojaków na suwnicy smitha, "
            "martwy ciąg z podwyższenia na smithie, rack pull smith"
        ),
        "back",
        ["lower back"],
        ["glutes", "hamstrings", "traps"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Set the safety stops just below the knees and start from them.",
            "Stand up with a flat back, lock out the hips, lower to the stops.",
        ],
    ),
    (
        "Smith Machine Front Squat",
        "Front Squat",
        "przysiad przedni na smithie, przysiad przedni na suwnicy smitha, front squat smith",
        "quads",
        ["quadriceps"],
        ["glutes"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Rest the bar on the front of your shoulders, elbows high.",
            "Squat down with an upright chest, then stand up.",
        ],
    ),
    (
        "Smith Machine Sumo Squat",
        None,
        (
            "przysiad sumo na smithie, przysiad sumo na suwnicy smitha, sumo squat smith, "
            "przysiad szeroki smith"
        ),
        "quads",
        ["quadriceps", "adductors"],
        ["glutes"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Wide stance, toes turned out, bar on your upper back.",
            "Squat down pushing the knees out in line with the toes, then stand up.",
        ],
    ),
    (
        "Smith Machine Box Squat",
        "Box Squat",
        (
            "przysiad na skrzynię na smithie, przysiad na skrzynię na suwnicy smitha, "
            "przysiad do skrzyni na smithie, box squat smith"
        ),
        "quads",
        ["quadriceps", "glutes"],
        ["hamstrings"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Put a box behind you, bar on your upper back.",
            "Sit back until you lightly touch the box, then stand up.",
        ],
    ),
    (
        "Smith Machine Hack Squat",
        "Barbell Hack Squat",
        (
            "przysiad hack na smithie, przysiad hack na suwnicy smitha, hack przysiad na smithie, "
            "hack squat smith, chair squat, przysiad na smithie ze stopami z przodu"
        ),
        "quads",
        ["quadriceps"],
        ["glutes"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Feet slightly in front of the bar, bar on your upper back.",
            "Lean back into the bar, squat down with knees forward, then stand up.",
        ],
    ),
    (
        "Smith Machine Kneeling Squat",
        "Kneeling Squat",
        (
            "przysiad na kolanach na smithie, przysiad na kolanach na suwnicy smitha, "
            "kneeling squat smith"
        ),
        "glutes",
        ["glutes"],
        ["quadriceps"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Kneel on a pad under the bar, bar on your upper back.",
            "Sit back towards your heels, then drive the hips forward to kneel upright.",
        ],
    ),
    (
        "Smith Machine Good Morning",
        "Good Morning",
        (
            "dzień dobry na smithie, dzień dobry na suwnicy smitha, "
            "skłony good morning na smithie, good morning smith"
        ),
        "hamstrings",
        ["hamstrings"],
        ["glutes", "lower back"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Bar on your upper back, knees soft.",
            "Push the hips back and lean forward with a flat back, then stand up.",
        ],
    ),
    (
        "Smith Machine Seated Calf Raise",
        "Barbell Seated Calf Raise",
        (
            "wspięcia na palce siedząc na smithie, wspięcia na palce siedząc na suwnicy smitha, "
            "łydki siedząc smith"
        ),
        "calves",
        ["calves"],
        [],
        "weight_reps",
        False,
        [
            SET_BAR,
            (
                "Sit on a bench, balls of the feet on a plate, padded bar across your lower "
                "thighs, just above the knees."
            ),
            "Raise your heels as high as you can, pause, lower slowly.",
        ],
    ),
    (
        "Smith Machine Donkey Calf Raise",
        "Donkey Calf Raises",
        (
            "wspięcia na palce w skłonie na smithie, "
            "wspięcia na palce w skłonie na suwnicy smitha, donkey calf raise smith"
        ),
        "calves",
        ["calves"],
        [],
        "weight_reps",
        False,
        [
            SET_BAR,
            (
                "Bend over with your hands on a bench for support and a flat back, the padded "
                "bar across the top of your hips, just above the tailbone; balls of the feet on "
                "a plate."
            ),
            "Raise your heels as high as you can, pause, lower slowly.",
        ],
    ),
    # --- back --------------------------------------------------------------------
    (
        "Smith Machine Shrug",
        "Barbell Shrug",
        "szrugsy na smithie, szrugsy na suwnicy smitha, wzruszanie ramion smith, kaptury smith",
        "back",
        ["traps"],
        [],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Hold the bar in front of your thighs, arms straight.",
            "Lift your shoulders towards your ears, pause, lower.",
        ],
    ),
    (
        "Smith Machine Inverted Row",
        "Inverted Row",
        (
            "podciąganie australijskie na smithie, podciąganie australijskie na suwnicy smitha, "
            "wiosłowanie w zwisie pod smithem, australijskie podciąganie smith"
        ),
        "back",
        ["middle back", "lats"],
        ["biceps"],
        "reps",
        False,
        [
            SET_BAR + " Set it about waist high.",
            "Hang under the bar with a straight body, heels on the floor.",
            "Pull your chest to the bar, lower with control.",
        ],
    ),
    (
        "Smith Machine Reverse-Grip Row",
        "Reverse Grip Bent-Over Rows",
        (
            "wiosłowanie podchwytem na smithie, wiosłowanie podchwytem na suwnicy smitha, "
            "wiosłowanie smith podchwyt"
        ),
        "back",
        ["middle back", "lats"],
        ["biceps"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Underhand grip, hinge forward with a flat back.",
            "Pull the bar to your lower stomach, lower with control.",
        ],
    ),
    # --- chest, shoulders, arms --------------------------------------------------
    (
        "Smith Machine Seated Shoulder Press",
        "Seated Barbell Military Press",
        (
            "wyciskanie nad głowę siedząc na smithie, "
            "wyciskanie nad głowę siedząc na suwnicy smitha, wyciskanie żołnierskie siedząc smith"
        ),
        "shoulders",
        ["shoulders"],
        ["triceps"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Sit on an upright bench under the bar, bar at chin height.",
            "Press the bar overhead, lower to the chin.",
        ],
    ),
    (
        "Smith Machine Incline Push-up",
        "Incline Push-Up",
        (
            "pompki na podwyższeniu na smithie, pompki na podwyższeniu na suwnicy smitha, "
            "pompki na drążku smitha, pompki na podwyższeniu smith"
        ),
        "chest",
        ["chest"],
        ["triceps", "shoulders"],
        "reps",
        False,
        [
            SET_BAR + " Higher bar = easier.",
            "Hands on the bar, body straight, feet on the floor.",
            "Lower your chest to the bar, push back up.",
        ],
    ),
    (
        "Smith Machine Floor Press",
        "Floor Press",
        (
            "wyciskanie z podłogi na smithie, wyciskanie z podłogi na suwnicy smitha, "
            "floor press smith"
        ),
        "chest",
        ["chest", "triceps"],
        ["shoulders"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Lie on the floor under the bar.",
            "Lower until your upper arms touch the floor, pause, press up.",
        ],
    ),
    (
        "Smith Machine Reverse-Grip Bench Press",
        None,
        (
            "wyciskanie podchwytem na smithie, wyciskanie podchwytem na suwnicy smitha, "
            "ławka podchwyt smith"
        ),
        "chest",
        ["chest"],
        ["triceps", "shoulders"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Lie on a flat bench, underhand grip shoulder-width apart.",
            "Lower the bar to your lower chest, press up.",
        ],
    ),
    (
        "Smith Machine Wide-Grip Bench Press",
        "Wide-Grip Barbell Bench Press",
        (
            "wyciskanie szerokim chwytem na smithie, "
            "wyciskanie szerokim chwytem na suwnicy smitha, ławka szeroko smith"
        ),
        "chest",
        ["chest"],
        ["shoulders", "triceps"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Lie on a flat bench, grip wider than shoulder width.",
            "Lower the bar to mid-chest, press up.",
        ],
    ),
    (
        "Smith Machine JM Press",
        "JM Press",
        "jm press na smithie, jm press na suwnicy smitha, wyciskanie jm smith",
        "triceps",
        ["triceps"],
        ["chest"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Lie on a flat bench, close grip.",
            "Bend the elbows and lower the bar towards your chin, elbows forward; press up.",
        ],
    ),
    (
        "Smith Machine Skull Crusher",
        "Skull Crusher",
        (
            "wyciskanie francuskie leżąc na smithie, "
            "wyciskanie francuskie leżąc na suwnicy smitha, "
            "wyciskanie francuskie na smithie, łamacze czaszki smith"
        ),
        "triceps",
        ["triceps"],
        [],
        "weight_reps",
        False,
        [
            SET_BAR,
            (
                "Lie on a flat bench so that the bar is over your forehead. Take a close grip, "
                "arms straight."
            ),
            "Bend only at the elbows to lower the bar towards your forehead, then extend.",
        ],
    ),
    (
        "Smith Machine Drag Curl",
        "Drag Curl",
        (
            "drag curl na smithie, drag curl na suwnicy smitha, "
            "uginanie ramion drag curl na smithie, drag curl smith"
        ),
        "biceps",
        ["biceps"],
        ["forearms"],
        "weight_reps",
        False,
        [
            SET_BAR,
            "Hold the bar at your thighs, underhand grip.",
            "Curl the bar up along your body, elbows moving back; lower slowly.",
        ],
    ),
]
