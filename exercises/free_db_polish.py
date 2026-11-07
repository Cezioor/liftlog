"""Polish names and synonyms for popular free-exercise-db exercises, keyed by source id.

The 65 original exercises have their own Polish names in seed_data.ALIASES; this list
covers the imported ones, so searching in Polish keeps working after the import.
"""

POLISH_NAMES = {
    # --- Chest ---
    "Wide-Grip_Barbell_Bench_Press": "wyciskanie sztangi szerokim chwytem",
    "Decline_Barbell_Bench_Press": "wyciskanie sztangi na skosie ujemnym, ławka skośna ujemna",
    "Decline_Dumbbell_Bench_Press": "wyciskanie hantli na skosie ujemnym",
    "Dumbbell_Bench_Press_with_Neutral_Grip": "wyciskanie hantli chwytem neutralnym",
    "Hammer_Grip_Incline_DB_Bench_Press": "wyciskanie hantli na skosie chwytem młotkowym",
    "Incline_Dumbbell_Flyes": "rozpiętki na ławce skośnej",
    "Decline_Dumbbell_Flyes": "rozpiętki na skosie ujemnym",
    "Flat_Bench_Cable_Flyes": "rozpiętki z linkami na ławce płaskiej",
    "Incline_Cable_Flye": "rozpiętki z linkami na ławce skośnej",
    "Low_Cable_Crossover": "krzyżowanie linek z dolnych wyciągów",
    "Single-Arm_Cable_Crossover": "krzyżowanie linek jednorącz",
    "Butterfly": "butterfly, motyl, rozpiętki na maszynie",
    "Leverage_Chest_Press": "wyciskanie na maszynie dźwigniowej",
    "Leverage_Incline_Chest_Press": "wyciskanie na maszynie skośnej",
    "Smith_Machine_Bench_Press": "wyciskanie na smithie, suwnica smitha ławka płaska",
    "Smith_Machine_Incline_Bench_Press": "wyciskanie na smithie na ławce skośnej",
    "Cable_Chest_Press": "wyciskanie na wyciągu",
    "Dumbbell_Floor_Press": "wyciskanie hantli leżąc na podłodze",
    "Floor_Press": "wyciskanie sztangi leżąc na podłodze, floor press",
    "Bent-Arm_Dumbbell_Pullover": "przenoszenie hantla za głowę, pullover",
    "Straight-Arm_Dumbbell_Pullover": "przenoszenie hantla prostymi rękami",
    "Push-Up_Wide": "pompki szerokie",
    "Push-Ups_-_Close_Triceps_Position": "pompki wąskie, pompki diamentowe",
    "Push-Ups_With_Feet_Elevated": "pompki z nogami na podwyższeniu",
    "Incline_Push-Up": "pompki na podwyższeniu, pompki skośne",
    "Plyo_Push-up": "pompki plyometryczne, pompki z klaśnięciem",
    "Handstand_Push-Ups": "pompki w staniu na rękach",
    "Bench_Dips": "pompki w podporze tyłem, dipy na ławce",
    "Dip_Machine": "dipy na maszynie, pompki na poręczach na maszynie",
    "Ring_Dips": "dipy na kółkach, pompki na kółkach",
    # --- Back ---
    "Close-Grip_Front_Lat_Pulldown": "ściąganie drążka wąskim chwytem",
    "V-Bar_Pulldown": "ściąganie uchwytu V na wyciągu górnym",
    "Underhand_Cable_Pulldowns": "ściąganie drążka podchwytem",
    "One_Arm_Lat_Pulldown": "ściąganie drążka jednorącz",
    "Wide-Grip_Pulldown_Behind_The_Neck": "ściąganie drążka za głowę",
    "Straight-Arm_Pulldown": "ściąganie drążka prostymi rękami, pullover na wyciągu",
    "Rope_Straight-Arm_Pulldown": "ściąganie liny prostymi rękami",
    "Bent_Over_Two-Dumbbell_Row": "wiosłowanie hantlami w opadzie",
    "Bent_Over_Two-Dumbbell_Row_With_Palms_In": "wiosłowanie hantlami chwytem neutralnym",
    "Reverse_Grip_Bent-Over_Rows": "wiosłowanie sztangą podchwytem",
    "Dumbbell_Incline_Row": "wiosłowanie hantlami na ławce skośnej, "
    "wiosłowanie z podparciem klatki",
    "Seated_One-arm_Cable_Pulley_Rows": "wiosłowanie jednorącz na wyciągu siedząc",
    "Elevated_Cable_Rows": "wiosłowanie na wyciągu z podwyższenia",
    "Leverage_High_Row": "wiosłowanie na maszynie z góry",
    "Leverage_Iso_Row": "wiosłowanie na maszynie dźwigniowej",
    "Smith_Machine_Bent_Over_Row": "wiosłowanie na smithie",
    "One-Arm_Long_Bar_Row": "wiosłowanie końcem sztangi jednorącz, landmine row",
    "Bent_Over_Two-Arm_Long_Bar_Row": "wiosłowanie końcem sztangi oburącz",
    "Cable_Rope_Rear-Delt_Rows": "wiosłowanie liną do twarzy",
    "Wide-Grip_Rear_Pull-Up": "podciąganie szerokim chwytem",
    "V-Bar_Pullup": "podciąganie z uchwytem V",
    "Muscle_Up": "muscle up, wejście siłowe",
    "Sumo_Deadlift": "martwy ciąg sumo",
    "Deficit_Deadlift": "martwy ciąg z deficytu, martwy ciąg z podwyższenia",
    "Rack_Pulls": "martwy ciąg ze stojaków, rack pull",
    "Trap_Bar_Deadlift": "martwy ciąg z trap barem, martwy ciąg sztangą heksagonalną",
    "Stiff-Legged_Barbell_Deadlift": "martwy ciąg na prostych nogach",
    "Stiff-Legged_Dumbbell_Deadlift": "martwy ciąg na prostych nogach z hantlami",
    "Good_Morning": "dzień dobry, skłony ze sztangą na plecach",
    "Reverse_Hyperextension": "odwrotne wyprosty, reverse hyper",
    "Hyperextensions_With_No_Hyperextension_Bench": "wyprosty tułowia bez ławki",
    # --- Shoulders ---
    "Barbell_Shoulder_Press": "wyciskanie sztangi nad głowę siedząc",
    "Seated_Barbell_Military_Press": "wyciskanie żołnierskie siedząc",
    "Push_Press": "wyciskanie z podrzutem, push press",
    "Standing_Dumbbell_Press": "wyciskanie hantli nad głowę stojąc",
    "Dumbbell_One-Arm_Shoulder_Press": "wyciskanie hantla nad głowę jednorącz",
    "Standing_Barbell_Press_Behind_Neck": "wyciskanie sztangi zza głowy",
    "Leverage_Shoulder_Press": "wyciskanie nad głowę na maszynie dźwigniowej",
    "Smith_Machine_Overhead_Shoulder_Press": "wyciskanie nad głowę na smithie",
    "Cable_Shoulder_Press": "wyciskanie nad głowę na wyciągu",
    "Front_Dumbbell_Raise": "wznosy przodem z hantlami, unoszenie ramion przodem",
    "Front_Cable_Raise": "wznosy przodem na wyciągu",
    "Standing_Front_Barbell_Raise_Over_Head": "unoszenie sztangi przodem nad głowę",
    "Seated_Side_Lateral_Raise": "wznosy bokiem siedząc",
    "One-Arm_Side_Laterals": "wznosy bokiem jednorącz",
    "Lateral_Raise_-_With_Bands": "wznosy bokiem z gumą",
    "Upright_Barbell_Row": "podciąganie sztangi wzdłuż tułowia",
    "Standing_Dumbbell_Upright_Row": "podciąganie hantli wzdłuż tułowia",
    "Upright_Cable_Row": "podciąganie linki wzdłuż tułowia",
    "Cable_Rear_Delt_Fly": "odwrotne rozpiętki na wyciągu",
    "Bent_Over_Low-Pulley_Side_Lateral": "wznosy bokiem w opadzie na wyciągu",
    "Dumbbell_Shrug": "szrugsy z hantlami, wzruszanie ramion z hantlami",
    "Cable_Shrugs": "szrugsy na wyciągu",
    "Smith_Machine_Behind_the_Back_Shrug": "szrugsy na smithie za plecami",
    "Band_Pull_Apart": "rozciąganie gumy przed sobą, pull apart",
    "External_Rotation": "rotacja zewnętrzna z hantlem",
    "External_Rotation_with_Cable": "rotacja zewnętrzna na wyciągu",
    # --- Biceps ---
    "EZ-Bar_Curl": "uginanie ramion sztangą łamaną, zgięcia ramion sztangą łamaną",
    "Close-Grip_EZ_Bar_Curl": "uginanie ramion sztangą łamaną wąsko",
    "Wide-Grip_Standing_Barbell_Curl": "uginanie ramion ze sztangą szeroko",
    "Reverse_Barbell_Curl": "uginanie ramion nachwytem, zgięcia ramion nachwytem",
    "Dumbbell_Alternate_Bicep_Curl": "uginanie ramion z hantlami naprzemiennie",
    "Alternate_Hammer_Curl": "uginanie młotkowe naprzemienne",
    "Cross_Body_Hammer_Curl": "uginanie młotkowe w poprzek tułowia",
    "Incline_Hammer_Curls": "uginanie młotkowe na ławce skośnej",
    "Concentration_Curls": "uginanie ramienia w koncentracji, koncentryczne uginanie",
    "Spider_Curl": "spider curl, uginanie ramion na ławce przodem",
    "Drag_Curl": "drag curl, uginanie ramion przy tułowiu",
    "Zottman_Curl": "uginanie zottmana",
    "Seated_Dumbbell_Curl": "uginanie ramion z hantlami siedząc",
    "Machine_Bicep_Curl": "uginanie ramion na maszynie",
    "Machine_Preacher_Curls": "modlitewnik na maszynie",
    "Cable_Preacher_Curl": "modlitewnik na wyciągu",
    "One_Arm_Dumbbell_Preacher_Curl": "modlitewnik jednorącz z hantlem",
    "Cable_Hammer_Curls_-_Rope_Attachment": "uginanie młotkowe na wyciągu z liną",
    "High_Cable_Curls": "uginanie ramion na górnych wyciągach",
    "Overhead_Cable_Curl": "uginanie ramion na wyciągu nad głową",
    "Standing_One-Arm_Cable_Curl": "uginanie ramienia jednorącz na wyciągu",
    # --- Triceps ---
    "Triceps_Pushdown_-_Rope_Attachment": "prostowanie ramion na wyciągu z liną",
    "Triceps_Pushdown_-_V-Bar_Attachment": "prostowanie ramion na wyciągu z uchwytem V",
    "Reverse_Grip_Triceps_Pushdown": "prostowanie ramion na wyciągu podchwytem",
    "Cable_One_Arm_Tricep_Extension": "prostowanie ramienia jednorącz na wyciągu",
    "Triceps_Overhead_Extension_with_Rope": "prostowanie ramion nad głową z liną",
    "Tricep_Dumbbell_Kickback": "prostowanie ramienia w opadzie, kickback",
    "Lying_Dumbbell_Tricep_Extension": "wyciskanie francuskie hantlami leżąc",
    "Standing_Overhead_Barbell_Triceps_Extension": "wyciskanie francuskie sztangą stojąc",
    "Machine_Triceps_Extension": "prostowanie ramion na maszynie",
    "JM_Press": "jm press",
    "Close-Grip_Dumbbell_Press": "wyciskanie hantli wąsko",
    "Tate_Press": "tate press",
    # --- Legs ---
    "Barbell_Full_Squat": "przysiad pełny ze sztangą, przysiad głęboki",
    "Box_Squat": "przysiad na skrzynię, box squat",
    "Wide_Stance_Barbell_Squat": "przysiad szeroki ze sztangą",
    "Zercher_Squats": "przysiad zerchera",
    "Overhead_Squat": "przysiad ze sztangą nad głową",
    "Smith_Machine_Squat": "przysiad na smithie",
    "Dumbbell_Squat": "przysiad z hantlami",
    "Plie_Dumbbell_Squat": "przysiad sumo z hantlem, przysiad plie",
    "Bodyweight_Squat": "przysiad bez obciążenia, przysiad z masą ciała",
    "Freehand_Jump_Squat": "przysiad z wyskokiem, wyskoki z przysiadu",
    "Weighted_Sissy_Squat": "przysiad sissy",
    "Barbell_Hack_Squat": "przysiad hack ze sztangą za plecami",
    "Narrow_Stance_Leg_Press": "suwnica wąsko, wypychanie nogami wąsko",
    "Barbell_Lunge": "wykroki ze sztangą",
    "Dumbbell_Rear_Lunge": "wykroki w tył z hantlami",
    "Barbell_Step_Ups": "wejścia na skrzynię ze sztangą",
    "Dumbbell_Step_Ups": "wejścia na skrzynię z hantlami, step up",
    "One_Leg_Barbell_Squat": "przysiad bułgarski ze sztangą, przysiad jednonóż ze sztangą",
    "Smith_Single-Leg_Split_Squat": "przysiad bułgarski na smithie",
    "Single-Leg_Leg_Extension": "prostowanie nogi jednonóż na maszynie",
    "Standing_Leg_Curl": "uginanie nogi stojąc na maszynie, zgięcia nogi stojąc",
    "Glute_Ham_Raise": "glute ham raise, ghr",
    "Thigh_Adductor": "przywodzenie nóg na maszynie, przywodziciele",
    "Thigh_Abductor": "odwodzenie nóg na maszynie, odwodziciele",
    "Cable_Hip_Adduction": "przywodzenie nogi na wyciągu",
    "Glute_Kickback": "wymach nogą w tył, kickback pośladków",
    "One-Legged_Cable_Kickback": "wymach nogą w tył na wyciągu",
    "Barbell_Glute_Bridge": "mostek biodrowy ze sztangą",
    "Kettlebell_One-Legged_Deadlift": "martwy ciąg na jednej nodze z kettlebell",
    "Standing_Barbell_Calf_Raise": "wspięcia na palce ze sztangą",
    "Standing_Dumbbell_Calf_Raise": "wspięcia na palce z hantlami",
    "Calf_Press_On_The_Leg_Press_Machine": "wspięcia na palce na suwnicy, łydki na suwnicy",
    "Smith_Machine_Calf_Raise": "wspięcia na palce na smithie",
    # --- Core ---
    "Crunches": "brzuszki, spięcia brzucha",
    "Sit-Up": "brzuszki pełne, siady z leżenia",
    "Reverse_Crunch": "odwrotne brzuszki, odwrotne spięcia brzucha",
    "Decline_Crunch": "brzuszki na ławce skośnej",
    "Oblique_Crunches": "skośne brzuszki",
    "Russian_Twist": "rosyjskie skręty, russian twist",
    "Ab_Crunch_Machine": "brzuszki na maszynie",
    "Flat_Bench_Lying_Leg_Raise": "unoszenie nóg leżąc na ławce",
    "Leg_Pull-In": "przyciąganie kolan do klatki leżąc",
    "Side_Bridge": "deska bokiem, plank boczny",
    "Dead_Bug": "martwy robak, dead bug",
    "Flutter_Kicks": "nożyce, nożyczki",
    "Standing_Cable_Wood_Chop": "drwal na wyciągu, wood chop",
    "Barbell_Ab_Rollout": "rolowanie sztangi, kółko ze sztangą",
    "Hanging_Pike": "unoszenie nóg w zwisie do drążka",
    "Dumbbell_Side_Bend": "skłony boczne z hantlem",
    "Jackknife_Sit-Up": "scyzoryki",
    # --- Olympic lifts and kettlebells ---
    "Clean_and_Jerk": "podrzut, zarzut i podrzut",
    "Snatch": "rwanie",
    "Power_Snatch": "rwanie siłowe",
    "Hang_Clean": "zarzut z zawieszenia",
    "Clean": "zarzut",
    "Split_Jerk": "podrzut nożycami",
    "Kettlebell_Windmill": "wiatrak z kettlebell",
    "Kettlebell_Turkish_Get-Up_Squat_style": "tureckie wstawanie, turkish get up",
    "Two-Arm_Kettlebell_Clean": "zarzut kettlebell oburącz",
    "One-Arm_Kettlebell_Snatch": "rwanie kettlebell jednorącz",
    "Kettlebell_Thruster": "thruster z kettlebell",
    "Front_Squats_With_Two_Kettlebells": "przysiad przedni z dwoma kettlebell",
    "Two-Arm_Kettlebell_Military_Press": "wyciskanie kettlebell nad głowę",
    "Kettlebell_Pistol_Squat": "pistolet z kettlebell, przysiad na jednej nodze",
    # --- Cardio ---
    "Rowing_Stationary": "wioślarz, ergometr wioślarski",
    "Running_Treadmill": "bieżnia, bieg na bieżni",
    "Walking_Treadmill": "chód na bieżni, marsz na bieżni",
    "Bicycling_Stationary": "rower stacjonarny",
    "Elliptical_Trainer": "orbitrek",
    "Stairmaster": "schody, stairmaster",
    # --- Chest and triceps (beginners, reviewed by the owner) ---
    "Chest_And_Front_Of_Shoulder_Stretch": (
        "rozciąganie klatki i przodu barków z kijem, stretching klatki, rozciąganie barków, "
        "kij za plecami"
    ),
    "Chest_Stretch_on_Stability_Ball": (
        "rozciąganie klatki na piłce gimnastycznej, stretching klatki, fitball, piłka szwajcarska"
    ),
    "Dynamic_Chest_Stretch": (
        "dynamiczne rozciąganie klatki, otwieranie klatki, wymachy ramion, rozgrzewka klatki"
    ),
    "Elbows_Back": "ściąganie łokci do tyłu, otwieranie klatki, łokcie w tył, rozciąganie klatki",
    "Chest_Push_multiple_response": (
        "seria pchnięć piłki lekarskiej z klęku, rzut piłką lekarską z klatki, medball, "
        "piłka lekarska"
    ),
    "Chest_Push_single_response": (
        "pchnięcie piłki lekarskiej z klęku, rzut piłką lekarską z klatki, medball, piłka lekarska"
    ),
    "Chest_Push_from_3_point_stance": (
        "pchnięcie piłki lekarskiej z pozycji trzypodporowej, rzut piłką lekarską, "
        "start z trzech podpór, medball"
    ),
    "Chest_Push_with_Run_Release": (
        "pchnięcie piłki lekarskiej z wybiegiem, rzut piłką lekarską, start z piłką, medball"
    ),
    "Medicine_Ball_Chest_Pass": (
        "podanie piłki lekarskiej sprzed klatki, rzut piłką lekarską, podania piłką lekarską, "
        "medball, chest pass"
    ),
    "Heavy_Bag_Thrust": "pchnięcie worka bokserskiego, worek treningowy, pchnięcia worka",
    "Incline_Push-Up_Depth_Jump": (
        "pompki z zeskokiem z podwyższenia, pompki plyometryczne, pompki z wyskokiem, depth jump"
    ),
    "Isometric_Chest_Squeezes": (
        "ściskanie dłoni przed klatką (izometria), izometria klatki, ściskanie dłoni, "
        "napinanie klatki"
    ),
    "Incline_Push-Up_Medium": (
        "pompki na podwyższeniu, pompki z rękami na podwyższeniu, pompki na ławce, "
        "łatwiejsze pompki, pompki dla początkujących"
    ),
    "Incline_Push-Up_Wide": (
        "pompki szerokie na podwyższeniu, szerokie pompki z rękami na podwyższeniu, "
        "pompki na ławce szeroko"
    ),
    "Incline_Push-Up_Reverse_Grip": (
        "pompki na podwyższeniu podchwytem, pompki z rękami na podwyższeniu podchwytem, "
        "pompki na podwyższeniu odwrotnym chwytem, pompki podchwytem"
    ),
    "Decline_Push-Up": (
        "pompki z nogami na podwyższeniu, pompki z nogami na ławce, pompki skośne w dół, "
        "decline push up"
    ),
    "Pushups_Close_and_Wide_Hand_Positions": (
        "pompki na zmianę wąsko i szeroko, pompki wąskie i szerokie, pompki zmiana chwytu"
    ),
    "Push_Up_to_Side_Plank": (
        "pompka z przejściem do deski bokiem, pompki z deską boczną, pompka z rotacją"
    ),
    "Suspended_Push-Up": "pompki na taśmach TRX, pompki trx, pompki na pasach",
    "Isometric_Wipers": (
        "przenoszenie ciężaru w podporze przodem, przenoszenie ciężaru w podporze, "
        "pompki izometryczne"
    ),
    "Bench_Press_-_With_Bands": (
        "wyciskanie gumy leżąc na ławce, wyciskanie z gumami, ławka z gumami, "
        "wyciskanie z oporem gum"
    ),
    "One_Arm_Dumbbell_Bench_Press": (
        "wyciskanie hantla jednorącz na ławce, wyciskanie hantla jednorącz na ławce płaskiej, "
        "wyciskanie jednorącz, wyciskanie jedną ręką"
    ),
    "Incline_Dumbbell_Bench_With_Palms_Facing_In": (
        "wyciskanie hantli na skosie chwytem młotkowym, "
        "wyciskanie hantli na ławce skośnej chwytem neutralnym, "
        "wyciskanie hantli skos chwytem młotkowym, chwyt neutralny"
    ),
    "Alternating_Floor_Press": (
        "naprzemienne wyciskanie kettlebell leżąc na podłodze, floor press z kettlebell, "
        "wyciskanie z podłogi naprzemiennie"
    ),
    "Extended_Range_One-Arm_Kettlebell_Floor_Press": (
        "wyciskanie kettlebell jednorącz leżąc na podłodze, floor press kettlebell jednorącz, "
        "wyciskanie z podłogi jedną ręką"
    ),
    "Incline_Cable_Chest_Press": (
        "wyciskanie na wyciągu skośnie w górę, wyciskanie linek skośnie, wyciąg na górną klatkę"
    ),
    "Standing_Cable_Chest_Press": (
        "wyciskanie na wyciągu stojąc, wyciskanie linek stojąc, wypychanie z wyciągów"
    ),
    "Leverage_Decline_Chest_Press": (
        "wyciskanie na maszynie na dolną klatkę, "
        "wyciskanie na maszynie dźwigniowej na dolną klatkę, maszyna skos ujemny, "
        "hammer na dolną klatkę"
    ),
    "Decline_Smith_Press": (
        "wyciskanie na smithie na skosie ujemnym, wyciskanie na suwnicy Smitha na skosie ujemnym, "
        "smith skos ujemny, wyciskanie na smithie głową w dół, dolna klatka smith"
    ),
    "Smith_Machine_Decline_Press": (
        "wyciskanie na smithie na skosie ujemnym, wyciskanie na suwnicy Smitha na skosie ujemnym, "
        "smith skos ujemny, wyciskanie na smithie głową w dół, dolna klatka smith"
    ),
    "Svend_Press": (
        "wyciskanie Svenda, svend press, ściskanie talerza przed klatką, wypychanie talerza"
    ),
    "One-Arm_Flat_Bench_Dumbbell_Flye": (
        "rozpiętki jednorącz na ławce płaskiej, rozpiętki jedną ręką, rozpiętki z hantlem jednorącz"
    ),
    "Incline_Dumbbell_Flyes_-_With_A_Twist": (
        "rozpiętki na ławce skośnej z rotacją, rozpiętki z hantlami na ławce skośnej z rotacją, "
        "rozpiętki skos z obrotem, rozpiętki z obrotem nadgarstków"
    ),
    "Cable_Iron_Cross": (
        "krzyżowanie linek z górnych wyciągów, iron cross, rozpiętki na bramie, brama, "
        "ściąganie linek"
    ),
    "Cross_Over_-_With_Bands": "rozpiętki z gumami, krzyżowanie gum, crossover z gumą",
    "Front_Raise_And_Pullover": (
        "unoszenie sztangi i przenoszenie za głowę leżąc, pullover ze sztangą, "
        "przenoszenie sztangi za głowę"
    ),
    "Triceps_Stretch": "rozciąganie tricepsa za głową, stretching tricepsa, łokieć za głową",
    "Tricep_Side_Stretch": (
        "rozciąganie tricepsa i barku w poprzek klatki, stretching tricepsa, ramię przez klatkę, "
        "rozciąganie barku"
    ),
    "Supine_Chest_Throw": (
        "wyrzut piłki lekarskiej w górę leżąc, rzut piłką lekarską leżąc, medball leżąc"
    ),
    "Parallel_Bar_Dip": (
        "pompki na poręczach na triceps, pompki na poręczach równoległych, dipy, poręcze, dips"
    ),
    "Dips_-_Triceps_Version": (
        "pompki na poręczach na triceps, dipy na triceps, poręcze tricepsowe, dips triceps"
    ),
    "Incline_Push-Up_Close-Grip": (
        "pompki wąskie na podwyższeniu, wąskie pompki z rękami na podwyższeniu, "
        "pompki diamentowe na podwyższeniu, pompki tricepsowe na ławce, pompki wąskie"
    ),
    "Body_Tricep_Press": (
        "wyciskanie francuskie z masą ciała, prostowanie ramion z masą ciała przy drążku, "
        "pompki tricepsowe na drążku, francuz z masą ciała, body triceps"
    ),
    "Band_Skull_Crusher": (
        "wyciskanie francuskie z gumą leżąc, skull crusher z gumą, francuz z gumą"
    ),
    "Cable_Lying_Triceps_Extension": (
        "wyciskanie francuskie na wyciągu leżąc, francuz na wyciągu leżąc, "
        "prostowanie ramion leżąc na wyciągu"
    ),
    "Low_Cable_Triceps_Extension": (
        "wyciskanie francuskie z liną na wyciągu, "
        "prostowanie ramion z liną na dolnym wyciągu leżąc, francuz na wyciągu z liną, lina leżąc"
    ),
    "Dumbbell_Tricep_Extension_-Pronated_Grip": (
        "wyciskanie francuskie hantlami nachwytem, wyciskanie francuskie hantli nachwytem leżąc, "
        "francuz hantlami nachwytem, francuz z hantlami leżąc"
    ),
    "One_Arm_Pronated_Dumbbell_Triceps_Extension": (
        "wyciskanie francuskie jednorącz nachwytem, "
        "wyciskanie francuskie hantla jednorącz nachwytem leżąc, francuz jednorącz nachwytem, "
        "francuz jedną ręką"
    ),
    "One_Arm_Supinated_Dumbbell_Triceps_Extension": (
        "wyciskanie francuskie jednorącz podchwytem, "
        "wyciskanie francuskie hantla jednorącz podchwytem leżąc, francuz jednorącz podchwytem, "
        "francuz jedną ręką"
    ),
    "Decline_Dumbbell_Triceps_Extension": (
        "wyciskanie francuskie hantlami na skosie ujemnym, "
        "wyciskanie francuskie hantli na ławce skośnej ujemnej, francuz hantlami skos ujemny"
    ),
    "Decline_EZ_Bar_Triceps_Extension": (
        "wyciskanie francuskie łamaną na skosie ujemnym, "
        "wyciskanie francuskie łamanej sztangi na skosie ujemnym, francuz łamaną skos ujemny, "
        "skull crusher skos ujemny, łamana"
    ),
    "Cable_Incline_Triceps_Extension": (
        "prostowanie ramion na wyciągu zza głowy na ławce skośnej, francuz na wyciągu skos, "
        "wyprosty zza głowy na wyciągu"
    ),
    "Seated_Triceps_Press": (
        "wyciskanie francuskie hantlem siedząc, wyciskanie francuskie hantla oburącz siedząc, "
        "francuz siedząc, prostowanie ramion zza głowy z hantlem"
    ),
    "Standing_One-Arm_Dumbbell_Triceps_Extension": (
        "prostowanie ramienia z hantlem zza głowy stojąc, francuz jednorącz stojąc, "
        "wyprost zza głowy jedną ręką"
    ),
    "Kettlebell_Overhead_Triceps_Extension": (
        "prostowanie ramion z kettlebell zza głowy, francuz z kettlebell, "
        "prostowanie ramion nad głową"
    ),
    "Speed_Band_Overhead_Triceps": (
        "szybkie prostowanie ramion z gumą zza głowy, francuz z gumą, guma nad głową"
    ),
    "Standing_Towel_Triceps_Extension": (
        "prostowanie ramion z ręcznikiem zza głowy, ćwiczenie z ręcznikiem, triceps bez sprzętu, "
        "francuz z ręcznikiem"
    ),
    "Sled_Overhead_Triceps_Extension": (
        "prostowanie ramion nad głową z saniami, sanie, sanki, prostowanie ramion z saniami"
    ),
    "Standing_Bent-Over_One-Arm_Dumbbell_Triceps_Extension": (
        "prostowanie ramienia w opadzie, prostowanie ramienia z hantlem w opadzie tułowia, "
        "kickback, kickback jednorącz, wyprost ramienia w opadzie"
    ),
    "Standing_Bent-Over_Two-Arm_Dumbbell_Triceps_Extension": (
        "prostowanie ramion w opadzie, prostowanie ramion z hantlami w opadzie tułowia, "
        "kickback oburącz, kickback z dwoma hantlami"
    ),
    "Seated_Bent-Over_One-Arm_Dumbbell_Triceps_Extension": (
        "prostowanie ramienia w opadzie siedząc, prostowanie ramienia z hantlem w opadzie siedząc, "
        "kickback siedząc, wyprost ramienia w opadzie siedząc"
    ),
    "Close-Grip_EZ-Bar_Press": (
        "wyciskanie łamanej sztangi wąskim chwytem, wąskie wyciskanie łamaną, wyciskanie wąsko ez"
    ),
    "Smith_Machine_Close-Grip_Bench_Press": (
        "wyciskanie wąskim chwytem na smithie, wyciskanie wąskim chwytem na suwnicy Smitha, "
        "wąskie wyciskanie na smithie, smith wąsko"
    ),
    # --- Shoulders (beginners, reviewed by the owner) ---
    "Arm_Circles": "krążenia ramion, krążenie rąk, rozgrzewka barków, kółka ramionami",
    "Elbow_Circles": "krążenia łokci, krążenia łokci z dłońmi na barkach, rozgrzewka barków",
    "Shoulder_Circles": "krążenia barków, rolowanie barków, krążenie barkami, rozgrzewka barków",
    "Shoulder_Raise": "unoszenie barków, wzruszanie ramion, szrugsy bez ciężaru, barki do uszu",
    "Upward_Stretch": "wyciąganie rąk w górę, rozciąganie w górę, przeciąganie się, ręce nad głowę",
    "Round_The_World_Shoulder_Stretch": (
        "przekładanie kija nad głową, przeprosty z kijem, przewijanie kija za plecami, "
        "dyslokacje z kijem, rozciąganie barków z kijem, kij nad głową"
    ),
    "Shoulder_Stretch": "rozciąganie barku w poprzek klatki, stretching barku, ramię przez klatkę",
    "Side_Wrist_Pull": (
        "rozciąganie barku za nadgarstek, rozciąganie barku z pociągnięciem nadgarstka, "
        "stretching barku, przeciąganie nadgarstka, rozciąganie pleców"
    ),
    "Chair_Upper_Body_Stretch": (
        "rozciąganie barków na krześle, stretching klatki na krześle, "
        "rozciąganie górnej części ciała"
    ),
    "Backward_Medicine_Ball_Throw": (
        "rzut piłką lekarską za siebie, rzut piłki za głowę, rzut do tyłu, medball, piłka lekarska"
    ),
    "Standing_Two-Arm_Overhead_Throw": (
        "rzut piłką lekarską zza głowy oburącz, wyrzut piłki zza głowy, medball, piłka lekarska"
    ),
    "Medicine_Ball_Scoop_Throw": (
        "wyrzut piłki lekarskiej w górę z przysiadu, scoop throw, medball, piłka lekarska"
    ),
    "Return_Push_from_Stance": (
        "łapanie i podanie piłki lekarskiej, odpychanie piłki lekarskiej z pozycji startowej, "
        "podania piłką lekarską w parze, medball, piłka lekarska"
    ),
    "Kneeling_Arm_Drill": (
        "praca ramion do sprintu w klęku, technika biegu, praca rąk w biegu, sprint"
    ),
    "Seated_Dumbbell_Press": (
        "wyciskanie hantli nad głowę siedząc, wyciskanie hantli siedząc, barki hantlami siedząc"
    ),
    "Standing_Alternating_Dumbbell_Press": (
        "naprzemienne wyciskanie hantli nad głowę, "
        "wyciskanie hantli nad głowę stojąc naprzemiennie, wyciskanie hantli naprzemiennie, "
        "wyciskanie jedną ręką na zmianę"
    ),
    "Standing_Palm-In_One-Arm_Dumbbell_Press": (
        "wyciskanie hantla nad głowę jednorącz chwytem neutralnym, "
        "wyciskanie hantla jednorącz stojąc, chwyt młotkowy, wyciskanie jedną ręką"
    ),
    "Alternating_Cable_Shoulder_Press": (
        "wyciskanie nad głowę na wyciągu naprzemiennie, wyciskanie linek nad głowę na zmianę"
    ),
    "Seated_Cable_Shoulder_Press": (
        "wyciskanie nad głowę na wyciągu siedząc, wyciskanie linek nad głowę siedząc"
    ),
    "Shoulder_Press_-_With_Bands": (
        "wyciskanie gumy nad głowę, wyciskanie z gumami nad głowę, barki z gumą"
    ),
    "Bradford_Rocky_Presses": (
        "wyciskanie Bradforda siedząc, bradford press, rocky press, wyciskanie przód i zza głowy, "
        "wyciskanie sztangi przód tył"
    ),
    "Standing_Bradford_Press": (
        "wyciskanie Bradforda stojąc, bradford press, wyciskanie przód i zza głowy, "
        "wyciskanie sztangi przód tył"
    ),
    "Dumbbell_Raise": (
        "wznosy bokiem z hantlami, wznosy bokiem, unoszenie hantli bokiem, boczne barki"
    ),
    "Power_Partials": (
        "niepełne wznosy bokiem z hantlami, power partials, półpowtórzenia wznosów, "
        "krótkie wznosy bokiem"
    ),
    "One-Arm_Incline_Lateral_Raise": (
        "wznosy bokiem jednorącz na ławce skośnej, wznosy bokiem leżąc bokiem na skosie, "
        "wznosy jedną ręką"
    ),
    "Standing_Low-Pulley_Deltoid_Raise": (
        "wznosy bokiem jednorącz na dolnym wyciągu, wznosy bokiem na wyciągu jedną ręką, "
        "boczne barki na wyciągu"
    ),
    "Front_Two-Dumbbell_Raise": (
        "wznosy przodem z hantlami oburącz, wznosy przodem obiema rękami, przednie barki"
    ),
    "Single_Dumbbell_Raise": (
        "wznosy przodem jednym hantlem oburącz, wznosy hantla przodem trzymanego oburącz, "
        "przednie barki"
    ),
    "Front_Incline_Dumbbell_Raise": (
        "wznosy przodem z hantlami na ławce skośnej, wznosy przodem leżąc na skosie, przednie barki"
    ),
    "Straight_Raises_on_Incline_Bench": (
        "wznosy sztangi leżąc przodem na skosie, "
        "wznosy przodem ze sztangą leżąc przodem na skosie, unoszenie sztangi przed głowę, "
        "wznosy sztangi na ławce skośnej"
    ),
    "Alternating_Deltoid_Raise": (
        "wznosy przodem i bokiem na zmianę, wznosy przodem i bokiem z hantlami, wznosy naprzemienne"
    ),
    "Side_Laterals_to_Front_Raise": (
        "wznosy przodem z rozłożeniem rąk na boki, wznosy przodem i bokiem, "
        "rozkładanie hantli na boki"
    ),
    "Dumbbell_Scaption": (
        "wznosy w płaszczyźnie łopatki, scaption, wznosy w literę Y, unoszenie ramion skośnie, "
        "stabilizacja łopatki"
    ),
    "Reverse_Flyes": (
        "odwrotne rozpiętki na ławce skośnej, odwrotne rozpiętki leżąc przodem na skosie, "
        "tylne aktony barków"
    ),
    "Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench": (
        "odwrotne rozpiętki z czołem na ławce, odwrotne rozpiętki w opadzie z czołem na ławce, "
        "odwrotne rozpiętki w opadzie, tylne aktony barków"
    ),
    "Reverse_Machine_Flyes": (
        "odwrotne rozpiętki na maszynie, reverse pec deck, odwrotny butterfly, "
        "tylne aktony na maszynie"
    ),
    "Back_Flyes_-_With_Bands": (
        "odwrotne rozpiętki z gumą, rozciąganie gumy na tylne aktony, tylne barki z gumą"
    ),
    "Sled_Reverse_Flye": "odwrotne rozpiętki z saniami, sanie, sanki, tylne aktony z saniami",
    "Barbell_Rear_Delt_Row": (
        "wiosłowanie sztangą na tylne aktony, wiosłowanie sztangą szerokim chwytem do klatki, "
        "wiosłowanie na tylne aktony, wiosłowanie sztangą do klatki, tylne barki"
    ),
    "Low_Pulley_Row_To_Neck": (
        "wiosłowanie liną do szyi na dolnym wyciągu, przyciąganie liny do szyi, "
        "wiosłowanie liną siedząc, tylne aktony"
    ),
    "External_Rotation_with_Band": (
        "rotacja zewnętrzna z gumą, rotatory z gumą, stożek rotatorów, rotacja barku na zewnątrz"
    ),
    "Internal_Rotation_with_Band": (
        "rotacja wewnętrzna z gumą, rotatory z gumą, stożek rotatorów, rotacja barku do środka"
    ),
    "Cable_Internal_Rotation": (
        "rotacja wewnętrzna na wyciągu, rotatory na wyciągu, stożek rotatorów, "
        "rotacja barku do środka"
    ),
    "Barbell_Incline_Shoulder_Raise": (
        "wypychanie barków ze sztangą na skosie, wypychanie barków ze sztangą na ławce skośnej, "
        "protrakcja łopatek, wysuwanie barków, zębaty przedni"
    ),
    "Dumbbell_Incline_Shoulder_Raise": (
        "wypychanie barków z hantlami na skosie, wypychanie barków z hantlami na ławce skośnej, "
        "protrakcja łopatek, wysuwanie barków, zębaty przedni"
    ),
    "Smith_Incline_Shoulder_Raise": (
        "wypychanie barków na smithie na skosie, wypychanie barków na smithie na ławce skośnej, "
        "protrakcja łopatek, wysuwanie barków, zębaty przedni"
    ),
    "Anti-Gravity_Press": (
        "wypychanie sztangi przed głowę leżąc przodem, "
        "wypychanie sztangi przed głowę leżąc przodem na skosie, anti-gravity press, "
        "wyciskanie przed siebie leżąc na ławce skośnej"
    ),
    "Smith_Machine_One-Arm_Upright_Row": (
        "podciąganie wzdłuż tułowia jednorącz na smithie, "
        "podciąganie sztangi wzdłuż tułowia jedną ręką, upright row"
    ),
    "Car_Drivers": (
        "kierownica z talerzem, car drivers, obracanie talerza, skręty talerza przed sobą"
    ),
    "Kettlebell_Halo": "halo z kettlebell, krążenie kettlebell wokół głowy, halo",
    "Kettlebell_Pirate_Ships": (
        "wymachy kettlebell na boki, pirate ships, statki pirackie, skręty z kettlebell"
    ),
    "Battling_Ropes": (
        "liny treningowe, liny bojowe, battle ropes, battling ropes, falowanie linami"
    ),
    "Sled_Overhead_Backward_Walk": (
        "chód tyłem z saniami z rękami w górze, sanie, sanki, chód tyłem z saniami"
    ),
    "Crucifix": (
        "trzymanie ciężarów w bok (krzyż), krzyż z ciężarami w bok, crucifix, "
        "utrzymanie ramion w bok, izometria barków, strongman"
    ),
    # --- Back and biceps (beginners, reviewed by the owner) ---
    "Cat_Stretch": "koci grzbiet, kot, cat cow, zaokrąglanie pleców w klęku podpartym",
    "Childs_Pose": (
        "pozycja dziecka, child's pose, balasana, rozciąganie pleców w siadzie na piętach"
    ),
    "Superman": "superman, łódka, unoszenie rąk i nóg leżąc na brzuchu, wyprosty leżąc",
    "Dynamic_Back_Stretch": "dynamiczne rozciąganie pleców, wymachy ramion, rozgrzewka pleców",
    "Upper_Back_Stretch": (
        "rozciąganie górnej części pleców, zaokrąglanie pleców z rękami przed sobą, "
        "stretching pleców"
    ),
    "Middle_Back_Stretch": "skręty tułowia stojąc, rozciąganie środka pleców, skręty w pasie",
    "Spinal_Stretch": (
        "skręty tułowia siedząc z rękami za głową, rozciąganie kręgosłupa, skręty na krześle"
    ),
    "Dancers_Stretch": (
        "skręt tułowia w siadzie z nogą założoną, skręt w siadzie, "
        "rozciąganie dolnej części pleców i pośladków"
    ),
    "Chair_Lower_Back_Stretch": (
        "skłon boczny na krześle, rozciąganie boku tułowia siedząc, rozciąganie lędźwi"
    ),
    "Side-Lying_Floor_Stretch": (
        "rozciąganie boku tułowia leżąc, rozciąganie boku leżąc bokiem, stretching boku"
    ),
    "Hug_Knees_To_Chest": (
        "obejmowanie kolan leżąc, kolana do klatki, przyciąganie kolan do klatki, "
        "rozciąganie dolnej części pleców"
    ),
    "Hug_A_Ball": (
        "przytulanie piłki w siadzie, rozciąganie pleców z piłką, fitball, piłka gimnastyczna"
    ),
    "Pyramid": "piramida na piłce, rozciąganie pleców na fitballu, piłka gimnastyczna",
    "Standing_Pelvic_Tilt": (
        "kołysanie miednicy stojąc, pelvic tilt, tyłopochylenie miednicy, ruchy miednicy"
    ),
    "One_Arm_Against_Wall": (
        "rozciąganie najszerszego przy ścianie, rozciąganie pleców przy framudze, "
        "stretching najszerszego"
    ),
    "One_Handed_Hang": (
        "rozciąganie w zwisie jednorącz, zwis na jednej ręce z podparciem nóg, "
        "rozciąganie najszerszego"
    ),
    "Latissimus_Dorsi-SMR": (
        "rolowanie najszerszego grzbietu, rolowanie pleców, roller, wałek, automasaż"
    ),
    "Lower_Back-SMR": "rolowanie dolnej części pleców, rolowanie lędźwi, roller, wałek, automasaż",
    "Overhead_Slam": (
        "slam piłką lekarską o ziemię, uderzenie piłką o podłogę, medball slam, slam ball, "
        "piłka lekarska"
    ),
    "Catch_and_Overhead_Throw": (
        "rzut piłką lekarską zza głowy i łapanie, rzut zza głowy o ścianę, medball, piłka lekarska"
    ),
    "Band_Assisted_Pull-Up": (
        "podciąganie na drążku z gumą, podciąganie z asystą gumy, guma do podciągania, "
        "łatwiejsze podciąganie"
    ),
    "Scapular_Pull-Up": (
        "podciąganie łopatkowe, ściąganie łopatek w zwisie, scapula pull up, aktywacja łopatek"
    ),
    "Kneeling_Single-Arm_High_Pulley_Row": (
        "ściąganie uchwytu jednorącz w klęku, ściąganie jednorącz na wyciągu górnym, "
        "wyciąg górny w klęku"
    ),
    "Cable_Incline_Pushdown": (
        "ściąganie drążka prostymi rękami na skosie, "
        "ściąganie drążka prostymi rękami na ławce skośnej, pullover na wyciągu leżąc, "
        "przenoszenie drążka za głowę"
    ),
    "Bent_Over_One-Arm_Long_Bar_Row": (
        "wiosłowanie końcem sztangi jednorącz, wiosłowanie końcem sztangi w opadzie, "
        "landmine jednorącz"
    ),
    "T-Bar_Row_with_Handle": (
        "wiosłowanie t-bar z uchwytem, t-bar row, landmine, wiosłowanie końcem sztangi z uchwytem"
    ),
    "Lying_Cambered_Barbell_Row": (
        "wiosłowanie sztangą leżąc na ławce, sztanga wygięta, "
        "wiosłowanie sztangą wygiętą leżąc przodem na ławce, wiosłowanie leżąc na ławce, "
        "cambered bar, wiosłowanie bez obciążania lędźwi"
    ),
    "Straight_Bar_Bench_Mid_Rows": (
        "wiosłowanie sztangą stojąc na ławce, wiosłowanie z ławki, "
        "wiosłowanie sztangą w opadzie z ławki"
    ),
    "Incline_Bench_Pull": (
        "wiosłowanie hantlami na skosie na tylne aktony, "
        "wiosłowanie hantlami na skosie łokciami na boki, przyciąganie hantli leżąc przodem, "
        "odwrotne wyciskanie, wiosłowanie na tylne aktony"
    ),
    "Kneeling_High_Pulley_Row": (
        "wiosłowanie liną z górnego wyciągu w klęku, przyciąganie liny w klęku, "
        "wiosłowanie liną z góry"
    ),
    "Shotgun_Row": (
        "wiosłowanie jednorącz na wyciągu w wykroku, "
        "wiosłowanie jednorącz na dolnym wyciągu w wykroku, shotgun row, "
        "wiosłowanie jedną ręką na wyciągu stojąc"
    ),
    "Inverted_Row": (
        "podciąganie australijskie, wiosłowanie w zwisie, australijskie podciąganie, "
        "wiosłowanie pod drążkiem"
    ),
    "Inverted_Row_with_Straps": (
        "podciąganie australijskie na taśmach, wiosłowanie w zwisie na taśmach, "
        "australijskie podciąganie na taśmach, trx, wiosłowanie na linach"
    ),
    "Suspended_Row": "wiosłowanie na taśmach TRX, trx row, wiosłowanie trx, wiosłowanie na pasach",
    "Sled_Row": "wiosłowanie z saniami, sanie, sanki, przyciąganie sań",
    "Barbell_Shrug_Behind_The_Back": (
        "szrugsy ze sztangą za plecami, szrugsy za plecami, wzruszanie ramion ze sztangą, kaptury"
    ),
    "Leverage_Shrug": (
        "szrugsy na maszynie, szrugsy na maszynie dźwigniowej, wzruszanie ramion na maszynie, "
        "kaptury"
    ),
    "Calf-Machine_Shoulder_Shrug": (
        "szrugsy na maszynie do łydek, szrugsy na suwnicy do łydek, wzruszanie ramion, kaptury"
    ),
    "Upright_Row_-_With_Bands": (
        "podciąganie gumy wzdłuż tułowia, upright row z gumą, podciąganie wzdłuż tułowia z gumą"
    ),
    "Smith_Machine_Upright_Row": (
        "podciąganie wzdłuż tułowia na smithie, upright row na smithie, "
        "podciąganie sztangi wzdłuż tułowia"
    ),
    "Stiff_Leg_Barbell_Good_Morning": (
        "dzień dobry na prostych nogach, good morning, skłony ze sztangą na karku, skłon ze sztangą"
    ),
    "Standing_Biceps_Stretch": (
        "rozciąganie bicepsa z rękami za plecami, stretching bicepsa, rozciąganie ramion"
    ),
    "Close-Grip_Standing_Barbell_Curl": (
        "uginanie ramion ze sztangą wąsko, uginanie sztangi wąskim chwytem, biceps wąsko"
    ),
    "Close-Grip_EZ-Bar_Curl_with_Band": (
        "uginanie ramion sztangą łamaną wąsko z gumą, uginanie łamanej z gumami, łamana z gumą"
    ),
    "Barbell_Curls_Lying_Against_An_Incline": (
        "uginanie sztangi leżąc przodem na skosie, "
        "uginanie ramion ze sztangą leżąc przodem na skosie, spider curl na ławce skośnej, "
        "uginanie sztangi na ławce skośnej"
    ),
    "Reverse_Plate_Curls": (
        "uginanie ramion z talerzem nachwytem, uginanie talerza, uginanie nachwytem z talerzem"
    ),
    "Reverse_Cable_Curl": (
        "uginanie ramion nachwytem na wyciągu, uginanie nachwytem na dolnym wyciągu"
    ),
    "Lying_Close-Grip_Bar_Curl_On_High_Pulley": (
        "uginanie ramion na górnym wyciągu leżąc, uginanie drążka wyciągu leżąc, "
        "biceps na wyciągu leżąc"
    ),
    "Alternate_Incline_Dumbbell_Curl": (
        "uginanie hantli na skosie naprzemiennie, uginanie ramion na ławce skośnej naprzemiennie"
    ),
    "Flexor_Incline_Dumbbell_Curls": (
        "uginanie na skosie z przesuniętym chwytem, "
        "uginanie ramion na ławce skośnej z przesuniętym chwytem, flexor curls, "
        "uginanie hantli na skosie"
    ),
    "Incline_Inner_Biceps_Curl": (
        "uginanie hantli na skosie z rozchyleniem rąk, "
        "uginanie ramion na ławce skośnej na zewnątrz, inner biceps curl, "
        "uginanie z rozchyleniem rąk"
    ),
    "Seated_Dumbbell_Inner_Biceps_Curl": (
        "uginanie hantli siedząc z rozchyleniem rąk, "
        "uginanie ramion z hantlami siedząc na zewnątrz, inner biceps curl siedząc, "
        "uginanie z rozchyleniem rąk"
    ),
    "Lying_Supine_Dumbbell_Curl": (
        "uginanie ramion z hantlami leżąc, uginanie hantli leżąc na plecach, biceps leżąc"
    ),
    "Standing_Concentration_Curl": (
        "uginanie ramienia w koncentracji stojąc, koncentracja stojąc, uginanie w opadzie jednorącz"
    ),
    "Preacher_Hammer_Dumbbell_Curl": (
        "uginanie młotkowe na modlitewniku, młotki na modlitewniku, hammer na modlitewniku"
    ),
    "Two-Arm_Dumbbell_Preacher_Curl": (
        "modlitewnik z hantlami, uginanie na modlitewniku z hantlami oburącz"
    ),
    "Standing_One-Arm_Dumbbell_Curl_Over_Incline_Bench": (
        "modlitewnik jednorącz na ławce skośnej, uginanie jednorącz przez oparcie ławki, "
        "modlitewnik na skosie"
    ),
    # --- Quads and calves (beginners, reviewed by the owner) ---
    "Ankle_Circles": "krążenia stóp, krążenia kostek, rozgrzewka stawu skokowego",
    "Knee_Circles": "krążenia kolan, krążenie kolanami, rozgrzewka kolan",
    "Calf_Stretch_Hands_Against_Wall": (
        "rozciąganie łydki przy ścianie, stretching łydki w wykroku, łydka o ścianę, "
        "dłonie na ścianie"
    ),
    "Calf_Stretch_Elbows_Against_Wall": (
        "rozciąganie łydek z łokciami o ścianę, stretching łydek, łydki przy ścianie, "
        "przedramiona na ścianie"
    ),
    "Seated_Calf_Stretch": (
        "rozciąganie łydki w siadzie, stretching łydki siedząc, przyciąganie stopy"
    ),
    "Standing_Gastrocnemius_Calf_Stretch": (
        "rozciąganie łydki z piętą na stopniu, mięsień brzuchaty łydki, stretching łydki, "
        "pięta na podwyższeniu"
    ),
    "Standing_Soleus_And_Achilles_Stretch": (
        "rozciąganie ścięgna Achillesa, mięsień płaszczkowaty, "
        "rozciąganie łydki z ugiętymi kolanami, achilles"
    ),
    "Calf_Raises_-_With_Bands": "wspięcia na palce z gumą, wspięcia z gumą oporową, łydki z gumą",
    "Barbell_Seated_Calf_Raise": (
        "wspięcia na palce siedząc ze sztangą, łydki siedząc ze sztangą na udach"
    ),
    "Dumbbell_Seated_One-Leg_Calf_Raise": (
        "wspięcia na palce siedząc jednonóż, wspięcia siedząc z hantlem na udzie, łydka jednonóż"
    ),
    "Rocking_Standing_Calf_Raise": (
        "wspięcia na palce i pięty ze sztangą, rocking calf raise, wspięcia z kołysaniem, "
        "unoszenie palców stóp"
    ),
    "Calf_Press": (
        "wypychanie palcami na maszynie, łydki na suwnicy, wspięcia na palce na maszynie, "
        "calf press, łydki na maszynie siedząc"
    ),
    "Smith_Machine_Reverse_Calf_Raises": (
        "unoszenie palców stóp na smithie, reverse calf raise, mięsień piszczelowy, "
        "wspięcia na pięty"
    ),
    "Balance_Board": (
        "stanie na desce balansowej, balance board, deska do balansu, równowaga, propriocepcja"
    ),
    "Jogging_Treadmill": "bieżnia, trucht na bieżni, jogging na bieżni, bieg na bieżni",
    "Recumbent_Bike": "rower poziomy, rower stacjonarny poziomy, recumbent, rower z oparciem",
    "Bicycling": "jazda na rowerze, rower, kolarstwo, rower szosowy",
    "Trail_Running_Walking": (
        "bieg w terenie, trail running, marsz w terenie, trekking, chodzenie po górach"
    ),
    "Sit_Squats": "półprzysiady, przysiady niepełne, szybkie półprzysiady, rozgrzewka nóg",
    "Rear_Leg_Raises": (
        "unoszenie nogi w tył w klęku podpartym, wymachy nogi w tył, prostowanie nogi w klęku"
    ),
    "Kneeling_Hip_Flexor": (
        "rozciąganie zginaczy biodra w klęku, stretching biodra, wykrok w klęku, zginacze bioder, "
        "biodro do przodu"
    ),
    "Standing_Hip_Flexors": (
        "rozciąganie zginaczy biodra stojąc, stretching biodra stojąc, zginacze bioder"
    ),
    "On_Your_Side_Quad_Stretch": (
        "rozciąganie czworogłowego leżąc bokiem, stretching uda, pięta do pośladka leżąc bokiem"
    ),
    "On-Your-Back_Quad_Stretch": (
        "rozciąganie czworogłowego leżąc na ławce, stretching uda, noga zwisająca z ławki"
    ),
    "One_Half_Locust": (
        "rozciąganie czworogłowego leżąc przodem, pół szarańczy, "
        "pięta do pośladka leżąc na brzuchu, stretching uda"
    ),
    "Standing_Elevated_Quad_Stretch": (
        "rozciąganie czworogłowego ze stopą na ławce, stretching uda, stopa na podwyższeniu z tyłu"
    ),
    "Looking_At_Ceiling": "wielbłąd, ustrasana, rozciąganie przodu ciała w klęku, ręce na piętach",
    "Standing_Long_Jump": "skok w dal z miejsca, skok obunóż w dal, skok w dal",
    "Side_Standing_Long_Jump": "skok w bok z miejsca, skok boczny w dal, skok w bok obunóż",
    "Rocket_Jump": "wyskok z rękami w górę, rocket jump, wyskok z półprzysiadu, wyskok dosiężny",
    "Star_Jump": "wyskok gwiazda, star jump, skok z rozłożeniem rąk i nóg",
    "Double_Leg_Butt_Kick": (
        "wyskok z piętami do pośladków, skok obunóż pięty do pośladków, butt kick"
    ),
    "Depth_Jump_Leap": "zeskok z wyskokiem na skrzynię, depth jump, skok w głąb, zeskok i wyskok",
    "Quick_Leap": (
        "wskok na skrzynię z wyskokiem, wskok na skrzynię, box jump, skok na skrzynię, "
        "wskoki na skrzynię"
    ),
    "Front_Cone_Hops_or_hurdle_hops": (
        "przeskoki przez pachołki obunóż, przeskoki przez płotki, hurdle hops, skoki przez pachołki"
    ),
    "Side_to_Side_Box_Shuffle": (
        "przeskoki boczne nad skrzynią, box shuffle, przeskoki przez skrzynię na boki"
    ),
    "Split_Jump": "wyskok z wykroku, split jump, wyskok w wykroku",
    "Scissors_Jump": (
        "wykroki z wyskokiem ze zmianą nóg, nożyce, skok nożycowy, jumping lunges, wykroki skakane"
    ),
    "Single_Leg_Butt_Kick": (
        "wyskok jednonóż z piętą do pośladka, butt kick jednonóż, skok na jednej nodze"
    ),
    "Single-Leg_Hop_Progression": (
        "skoki jednonóż przez pachołki, skoki na jednej nodze, hop jednonóż"
    ),
    "Single-Leg_Lateral_Hop": (
        "przeskoki boczne jednonóż, przeskoki jednonóż przez pachołek, skoki w bok na jednej nodze"
    ),
    "Side_Hop-Sprint": "przeskoki boczne ze sprintem, przeskoki w bok przez płotek i sprint",
    "Alternate_Leg_Diagonal_Bound": (
        "wieloskok naprzemienny na skos, bounding, skoki z nogi na nogę na boki, wieloskoki"
    ),
    "Fast_Skipping": "szybkie podskoki naprzemienne, skipping, skip, podskoki",
    "Single-Cone_Sprint_Drill": "sprint dookoła pachołka, szybkie stopy, praca nóg, drobienie",
    "Bench_Sprint": (
        "szybka zmiana nóg na skrzyni, bench sprint, szybkie wejścia na skrzynię, "
        "zmiana nóg na ławce"
    ),
    "Single_Leg_Push-off": (
        "wybicia z nogi opartej na skrzyni, wybicie jednonóż ze skrzyni, push off, "
        "wybicie z nogi na skrzyni"
    ),
    "Single-Leg_Stride_Jump": (
        "wyskok z nogą na skrzyni, stride jump, wybicie z nogi na skrzyni w górę"
    ),
    "Stride_Jump_Crossover": (
        "wyskok nad skrzynią z przejściem, stride jump crossover, "
        "przeskok nad skrzynią na drugą stronę"
    ),
    "Single-Leg_High_Box_Squat": (
        "wejścia jednonóż na wysoką skrzynię, przysiad jednonóż na skrzyni, "
        "wejścia na skrzynię jedną nogą"
    ),
    "Squats_-_With_Bands": "przysiad z gumą, przysiad z gumami, przysiad z gumą oporową",
    "Barbell_Side_Split_Squat": (
        "przysiad boczny ze sztangą, wykrok w bok ze sztangą, przysiad kozacki ze sztangą"
    ),
    "Chair_Squat": (
        "przysiad ze stopami wysuniętymi w przód, chair squat, "
        "przysiad na maszynie ze stopami z przodu"
    ),
    "Barbell_Walking_Lunge": "wykroki chodzone ze sztangą, wykroki w marszu ze sztangą",
    "Bodyweight_Walking_Lunge": (
        "wykroki chodzone bez obciążenia, wykroki w marszu, wykroki z rękami na biodrach"
    ),
    "Cable_Deadlifts": (
        "martwy ciąg na wyciągu, martwy ciąg z linkami, martwy ciąg z dolnych wyciągów"
    ),
    "Leverage_Deadlift": "martwy ciąg na maszynie, martwy ciąg na maszynie dźwigniowej",
    "Hip_Flexion_with_Band": (
        "unoszenie kolana z gumą, zginanie biodra z gumą, zginacze biodra, kolano w górę z gumą"
    ),
    "Sled_Push": "pchanie sań, sanie, sanki, sled push, prowler",
    "Backward_Drag": "ciągnięcie sań tyłem, sanie, sanki, chód tyłem z saniami",
    "Sled_Drag_-_Harness": "ciągnięcie sań w uprzęży, sanie, sanki, uprząż, ciągnięcie sań",
    "Bear_Crawl_Sled_Drags": (
        "czworakowanie z saniami, bear crawl, chód niedźwiedzia z saniami, sanie"
    ),
    "Sandbag_Load": (
        "przenoszenie worka na podest, sandbag, worek z piaskiem, strongman, ładowanie worka"
    ),
    "Mountain_Climbers": "bieg w podporze, mountain climbers, wspinacz, wspinaczka",
    # --- Hamstrings, glutes and forearms (beginners, reviewed by the owner) ---
    "Front_Leg_Raises": (
        "wymachy nogi w przód, wymachy nóg, rozgrzewka bioder, wymachy prostej nogi"
    ),
    "Inchworm": "gąsienica, inchworm, spacer dłońmi do podporu, przejście do podporu",
    "Standing_Toe_Touches": (
        "skłon do palców stojąc, dotykanie palców stóp, skłon w przód, rozciąganie tyłu nóg"
    ),
    "Seated_Floor_Hamstring_Stretch": (
        "skłon do nogi w siadzie, rozciąganie dwugłowych siedząc, skłon do wyprostowanej nogi"
    ),
    "The_Straddle": (
        "siad rozkroczny ze skłonem, rozkrok w siadzie, szpagat poprzeczny siedząc, "
        "rozciąganie przywodzicieli"
    ),
    "Upper_Back-Leg_Grab": (
        "skłon z objęciem ud w siadzie, skłon w siadzie, rozciąganie pleców i dwugłowych"
    ),
    "Runners_Stretch": "rozciąganie biegacza, wykrok rozciągający, rozciąganie dwugłowych i łydki",
    "Hamstring_Stretch": (
        "rozciąganie dwugłowych z paskiem leżąc, rozciąganie tyłu uda, pasek, taśma, guma, "
        "stretching dwugłowych"
    ),
    "Leg-Up_Hamstring_Stretch": (
        "rozciąganie dwugłowych z nogą w górze, rozciąganie tyłu uda leżąc, noga do nosa"
    ),
    "90_90_Hamstring": (
        "prostowanie nogi 90/90 leżąc, rozciąganie dwugłowych 90/90, stretching tyłu uda"
    ),
    "Standing_Hamstring_and_Calf_Stretch": (
        "rozciąganie tyłu nogi z paskiem stojąc, rozciąganie dwugłowych i łydki, pasek, taśma"
    ),
    "Chair_Leg_Extended_Stretch": (
        "odwodzenie wyprostowanej nogi siedząc, rozciąganie na krześle, noga w bok siedząc"
    ),
    "Hamstring-SMR": "rolowanie dwugłowych, rolowanie tyłu uda, roller, wałek, automasaż",
    "Ball_Leg_Curl": (
        "uginanie nóg na piłce, leg curl na fitballu, piłka gimnastyczna, "
        "uginanie nóg leżąc na piłce"
    ),
    "Platform_Hamstring_Slides": (
        "uginanie nogi ze ślizgiem leżąc, ślizgi piętą, slider, uginanie nogi na podłodze"
    ),
    "Seated_Band_Hamstring_Curl": (
        "uginanie nóg siedząc z gumą, leg curl z gumą, uginanie nóg z gumą"
    ),
    "Prone_Manual_Hamstring": (
        "uginanie nogi leżąc z oporem partnera, uginanie nogi z partnerem, opór partnera"
    ),
    "Band_Good_Morning": "dzień dobry z gumą, good morning z gumą, skłony z gumą",
    "Band_Good_Morning_Pull_Through": (
        "dzień dobry z gumą przy słupku, przeciąganie gumy w skłonie, good morning pull through, "
        "dzień dobry z gumą od słupka"
    ),
    "Smith_Machine_Stiff-Legged_Deadlift": (
        "martwy ciąg na prostych nogach na smithie, martwy ciąg na sztywnych nogach na smithie, "
        "smith"
    ),
    "Front_Box_Jump": "wskok na skrzynię, box jump, skok na skrzynię, wskoki na skrzynię",
    "Box_Jump_Multiple_Response": (
        "seria wskoków na skrzynię, box jump seria, wskoki na skrzynię seriami"
    ),
    "Box_Skip": "przeskoki z nogi na nogę przez skrzynie, box skip, wieloskoki przez skrzynie",
    "Hurdle_Hops": (
        "przeskoki przez pachołki obunóż, przeskoki przez płotki, hurdle hops, skoki przez płotki"
    ),
    "Knee_Tuck_Jump": (
        "wyskok z kolanami do klatki, tuck jump, skok kuczny, wyskok z podciągnięciem kolan"
    ),
    "Vertical_Swing": "wymach hantlem z wyskokiem, swing hantlem z wyskokiem, wyskok z hantlem",
    "Linear_3-Part_Start_Technique": (
        "start do sprintu z trzech podpór, start niski, start do sprintu, technika startu"
    ),
    "Linear_Acceleration_Wall_Drill": (
        "ćwiczenie startowe przy ścianie, wbijanie kolana przy ścianie, przyspieszenie, sprint"
    ),
    "Moving_Claw_Series": "bieg z zagarnianiem stopy, claw drill, technika biegu, zagarnianie",
    "Prowler_Sprint": "sprint z saniami, prowler, pchanie sań sprintem, sanie",
    "Hip_Circles_prone": (
        "krążenia biodra w klęku podpartym, krążenia kolanem w klęku, rozgrzewka bioder"
    ),
    "Standing_Hip_Circles": (
        "krążenia biodra stojąc, otwieranie biodra, krążenia kolanem stojąc, rozgrzewka bioder"
    ),
    "Side_Leg_Raises": (
        "wymachy nogi w bok, odwodzenie nogi stojąc, rozgrzewka bioder, wymachy nóg na boki"
    ),
    "Ankle_On_The_Knee": (
        "rozciąganie pośladka w pozycji czwórki, figure 4, czwórka, kostka na kolanie, "
        "mięsień gruszkowaty"
    ),
    "Knee_Across_The_Body": (
        "skręt z kolanem w poprzek ciała leżąc, skręt kręgosłupa leżąc, "
        "rozciąganie pośladka i pleców"
    ),
    "One_Knee_To_Chest": (
        "obejmowanie kolana leżąc, kolano do klatki, przyciąganie kolana do klatki, "
        "rozciąganie pośladka"
    ),
    "Side_Lying_Groin_Stretch": (
        "rozciąganie pachwiny leżąc bokiem, rozciąganie przywodzicieli, pachwina"
    ),
    "Lateral_Bound": "skoki łyżwiarza, lateral bound, skoki z nogi na nogę w bok, łyżwiarz",
    "Lateral_Box_Jump": (
        "przeskok boczny przez skrzynię, przeskoki w bok przez skrzynię, lateral box jump"
    ),
    "Lateral_Cone_Hops": (
        "przeskoki boczne przez pachołki, przeskoki w bok obunóż, skoki w bok przez pachołki"
    ),
    "Carioca_Quick_Step": "carioca, krok skrzyżny, przeplatanka, szybkie kroki skrzyżne",
    "Single_Leg_Glute_Bridge": (
        "mostek biodrowy jednonóż, mostek na jednej nodze, unoszenie bioder jednonóż"
    ),
    "Hip_Lift_with_Band": "mostek biodrowy z gumą, unoszenie bioder z gumą, mostek z oporem gumy",
    "Physioball_Hip_Bridge": (
        "wypychanie bioder na piłce, mostek biodrowy na piłce, hip thrust na fitballu, "
        "piłka gimnastyczna"
    ),
    "Hip_Extension_with_Bands": (
        "prostowanie nogi w tył z gumą, wymach nogą w tył z gumą, prostowanie biodra z gumą, "
        "kickback z gumą"
    ),
    "Band_Hip_Adductions": "przywodzenie nogi z gumą, przywodziciele z gumą, przywodzenie stojąc",
    "Monster_Walk": "monster walk, chód potwora, chód z gumą, spacer z gumą na kostkach",
    "Leg_Lift": (
        "uginanie nogi stojąc, przyciąganie pięty do pośladka stojąc, uginanie nogi bez maszyny"
    ),
    "Step-up_with_Knee_Raise": (
        "wejścia na skrzynię z uniesieniem kolana, wejście z kolanem, "
        "wejścia na ławkę z kolanem w górę"
    ),
    "Wrist_Circles": "krążenia nadgarstków, rozgrzewka nadgarstków, kółka nadgarstkami",
    "Kneeling_Forearm_Stretch": (
        "rozciąganie przedramion w klęku, stretching nadgarstków, "
        "dłonie na podłodze palcami do kolan"
    ),
    "Seated_Dumbbell_Palms-Down_Wrist_Curl": (
        "prostowanie nadgarstków z hantlami, uginanie nadgarstków nachwytem, "
        "prostowanie nadgarstków, reverse wrist curl, nadgarstki z hantlami nachwytem"
    ),
    "Seated_One-Arm_Dumbbell_Palms-Up_Wrist_Curl": (
        "uginanie nadgarstka jednorącz, uginanie nadgarstka z hantlem, wrist curl jednorącz"
    ),
    "Seated_Palm-Up_Barbell_Wrist_Curl": (
        "uginanie nadgarstków ze sztangą, wrist curl ze sztangą, nadgarstki siedząc"
    ),
    "Seated_Palms-Down_Barbell_Wrist_Curl": (
        "prostowanie nadgarstków ze sztangą, uginanie nadgarstków nachwytem, "
        "uginanie nadgarstków nachwytem ze sztangą, reverse wrist curl"
    ),
    "Palms-Up_Barbell_Wrist_Curl_Over_A_Bench": (
        "uginanie nadgarstków przez ławkę, uginanie nadgarstków ze sztangą w klęku, "
        "przedramiona na ławce"
    ),
    "Palms-Down_Wrist_Curl_Over_A_Bench": (
        "prostowanie nadgarstków przez ławkę, uginanie nadgarstków nachwytem, "
        "uginanie nadgarstków nachwytem przez ławkę, prostowanie nadgarstków ze sztangą w klęku, "
        "przedramiona na ławce"
    ),
    "Palms-Up_Dumbbell_Wrist_Curl_Over_A_Bench": (
        "uginanie nadgarstków z hantlami przez ławkę, uginanie nadgarstków z hantlami w klęku"
    ),
    "Palms-Down_Dumbbell_Wrist_Curl_Over_A_Bench": (
        "prostowanie nadgarstków z hantlami przez ławkę, uginanie nadgarstków nachwytem, "
        "uginanie nadgarstków nachwytem z hantlami, prostowanie nadgarstków z hantlami, "
        "przez ławkę w klęku"
    ),
    "Standing_Palms-Up_Barbell_Behind_The_Back_Wrist_Curl": (
        "uginanie nadgarstków ze sztangą za plecami, wrist curl za plecami, nadgarstki stojąc"
    ),
    "Cable_Wrist_Curl": (
        "uginanie nadgarstków na wyciągu, wrist curl na wyciągu, nadgarstki na dolnym wyciągu"
    ),
    "Seated_Two-Arm_Palms-Up_Low-Pulley_Wrist_Curl": (
        "uginanie nadgarstków na wyciągu siedząc, wrist curl na dolnym wyciągu siedząc"
    ),
    "Finger_Curls": "uginanie palców ze sztangą, finger curls, siła palców, chwyt",
    "Wrist_Rotations_with_Straight_Bar": "obracanie sztangi w dłoniach, nadgarstki naprzemiennie",
    "Wrist_Roller": (
        "zwijanie linki z ciężarkiem, wrist roller, roller do przedramion, nawijanie linki"
    ),
    "Standing_Olympic_Plate_Hand_Squeeze": (
        "ściskanie talerzy w dłoniach, chwyt szczypcowy, pinch grip, przedramiona, siła chwytu"
    ),
    # --- Core, neck and full body (beginners, reviewed by the owner) ---
    "Stomach_Vacuum": "vacuum brzucha, wciąganie brzucha, próżnia brzuszna, stomach vacuum",
    "Lower_Back_Curl": (
        "wyprost tułowia leżąc przodem, unoszenie tułowia leżąc na brzuchu, wyprosty leżąc, "
        "prostowniki"
    ),
    "Overhead_Stretch": (
        "wyciąganie tułowia z rękami w górze, rozciąganie tułowia, przeciąganie się, "
        "dłonie do sufitu"
    ),
    "Standing_Lateral_Stretch": (
        "skłon boczny stojąc, rozciąganie boku tułowia stojąc, ręka za głową"
    ),
    "Seated_Overhead_Stretch": (
        "skłon boczny w siadzie motylkowym, rozciąganie boku w siadzie, motylek, ręka za głową"
    ),
    "Torso_Rotation": (
        "skręty tułowia z piłką, skręty stojąc z piłką, rotacja tułowia, rozgrzewka tułowia"
    ),
    "Toe_Touchers": "sięganie do palców leżąc, toe touch, brzuszki do stóp, nogi w górze",
    "Scissor_Kick": (
        "nożyce pionowe, nożyce szerokie, scissor kick, nożyczki, naprzemienne unoszenie nóg leżąc"
    ),
    "Supine_Two-Arm_Overhead_Throw": (
        "rzut piłką lekarską oburącz z leżenia, brzuszek z rzutem, medball, piłka lekarska"
    ),
    "Supine_One-Arm_Overhead_Throw": (
        "rzut piłką lekarską jednorącz z leżenia, brzuszek z rzutem jedną ręką, medball, "
        "piłka lekarska"
    ),
    "One-Arm_Medicine_Ball_Slam": (
        "slam piłką lekarską jednorącz, uderzenie piłką o podłogę jedną ręką, medball slam"
    ),
    "Medicine_Ball_Full_Twist": (
        "podania piłki ze skrętem w parze, podawanie piłki plecami do partnera, medball, "
        "piłka lekarska"
    ),
    "Sledgehammer_Swings": "uderzenia młotem w oponę, młot, opona, sledgehammer, strongman",
    "3_4_Sit-Up": "brzuszki 3/4, niepełne siady z leżenia, sit up 3/4",
    "Janda_Sit-Up": "brzuszki Jandy, janda sit up, brzuszki z napiętymi pośladkami",
    "Weighted_Crunches": "brzuszki z obciążeniem, brzuszki z ciężarem, brzuszki z talerzem",
    "Otis-Up": "brzuszki z wypchnięciem ciężaru, otis up, brzuszki z talerzem nad głowę",
    "Crunch_-_Hands_Overhead": "brzuszki z rękami nad głową, brzuszki z wyprostowanymi rękami",
    "Crunch_-_Legs_On_Exercise_Ball": (
        "brzuszki z nogami na piłce, brzuszki z nogami na fitballu, piłka gimnastyczna"
    ),
    "Exercise_Ball_Crunch": "brzuszki na piłce, brzuszki na fitballu, piłka gimnastyczna",
    "Tuck_Crunch": "brzuszki z nogami w górze, brzuszki ze skrzyżowanymi nogami w górze",
    "Cocoons": "scyzoryk z ugiętymi nogami, cocoons, kokony, brzuszki kokon, scyzoryk z kolanami",
    "Air_Bike": "rowerek, brzuszki rowerowe, air bike, bicycle crunch, rowerek leżąc",
    "Cross-Body_Crunch": "brzuszki krzyżowe, łokieć do kolana, cross body crunch, skośne brzuszki",
    "Elbow_to_Knee": "brzuszki łokieć do kolana z nogą założoną, łokieć do kolana, skośne brzuszki",
    "Alternate_Heel_Touchers": (
        "sięganie do pięt naprzemiennie, heel touches, skośne brzuszki do pięt"
    ),
    "Oblique_Crunches_-_On_The_Floor": (
        "skośne brzuszki leżąc bokiem, brzuszki bokiem, skośne brzuszki na podłodze"
    ),
    "Decline_Oblique_Crunch": "skośne brzuszki na ławce skośnej, brzuszki skośne na skosie",
    "Side_Jackknife": "scyzoryki bokiem, side jackknife, scyzoryk na boku",
    "Decline_Reverse_Crunch": (
        "odwrotne brzuszki na ławce skośnej, odwrotne brzuszki na skosie, "
        "unoszenie bioder na skosie"
    ),
    "Cable_Reverse_Crunch": "odwrotne brzuszki na wyciągu, odwrotne brzuszki z linką przy kostkach",
    "Smith_Machine_Hip_Raise": "odwrotne brzuszki na smithie, unoszenie bioder na smithie",
    "Bent-Knee_Hip_Raise": (
        "przyciąganie ugiętych nóg leżąc, odwrotne brzuszki, unoszenie kolan leżąc, dolny brzuch"
    ),
    "Bottoms_Up": "unoszenie bioder z nogami w górę, bottoms up, odwrotne brzuszki z wyprostem nóg",
    "Flat_Bench_Leg_Pull-In": (
        "przyciąganie kolan do klatki leżąc, przyciąganie kolan na ławce, leg pull in"
    ),
    "Seated_Flat_Bench_Leg_Pull-In": (
        "przyciąganie kolan siedząc, scyzoryk siedząc, seated tucks, "
        "przyciąganie kolan na ławce siedząc"
    ),
    "Seated_Leg_Tucks": (
        "przyciąganie kolan siedząc, scyzoryk siedząc, seated tucks, "
        "przyciąganie kolan na ławce siedząc"
    ),
    "Exercise_Ball_Pull-In": (
        "przyciąganie kolan na piłce, scyzoryk na piłce, ball pull in, fitball w podporze"
    ),
    "Suspended_Reverse_Crunch": (
        "przyciąganie kolan na taśmach TRX, odwrotne brzuszki trx, kolana do klatki w podporze"
    ),
    "Knee_Hip_Raise_On_Parallel_Bars": (
        "unoszenie nóg na poręczach, kapitańskie krzesło, captain's chair, "
        "unoszenie kolan na poręczach"
    ),
    "Wind_Sprints": (
        "naprzemienne unoszenie kolan w zwisie, unoszenie kolan w zwisie na zmianę, bieg w zwisie"
    ),
    "Butt-Ups": "unoszenie bioder w desce, butt ups, deska z unoszeniem pośladków",
    "Spider_Crawl": "spiderman w podporze, spider crawl, kolano do łokcia w podporze, spiderman",
    "Rope_Crunch": (
        "spięcia brzucha na wyciągu, allahy, brzuszki na wyciągu z liną, "
        "brzuszki w klęku na wyciągu"
    ),
    "Standing_Rope_Crunch": (
        "spięcia brzucha na wyciągu stojąc, brzuszki na wyciągu stojąc, lina za głową"
    ),
    "Cable_Seated_Crunch": "spięcia brzucha na wyciągu siedząc, brzuszki na wyciągu siedząc, lina",
    "Kneeling_Cable_Crunch_With_Alternating_Oblique_Twists": (
        "spięcia brzucha na wyciągu ze skrętem, allahy ze skrętem, skośne na wyciągu"
    ),
    "Bosu_Ball_Cable_Crunch_With_Side_Bends": (
        "spięcia brzucha na bosu z wyciągiem, bosu, brzuszki na bosu z linkami, skłony boczne"
    ),
    "One-Arm_High-Pulley_Cable_Side_Bends": (
        "skłony boczne na górnym wyciągu, skłony boczne jednorącz na wyciągu"
    ),
    "Cable_Russian_Twists": (
        "rosyjskie skręty na wyciągu, russian twist na wyciągu, skręty na piłce z linką"
    ),
    "Pallof_Press_With_Rotation": (
        "wyciskanie pallofa ze skrętem, pallof press z rotacją, antyrotacja"
    ),
    "Standing_Cable_Lift": "drwal z dołu na wyciągu, cable lift, odwrotny drwal, wood chop z dołu",
    "Cable_Judo_Flip": "rzut judo na wyciągu, judo flip, skręt z liną przez ramię",
    "Barbell_Side_Bend": "skłony boczne ze sztangą, skłony na boki ze sztangą na karku",
    "Seated_Barbell_Twist": "skręty ze sztangą na karku siedząc, skręty tułowia ze sztangą",
    "Landmine_180s": "skręty tułowia z landmine, landmine 180, rainbow, obroty sztangi na boki",
    "Spell_Caster": "skręty tułowia z hantlami, spell caster, czarodziej, wymachy hantli na boki",
    "Isometric_Neck_Exercise_-_Front_And_Back": (
        "izometria szyi przód i tył, wzmacnianie szyi, napinanie szyi dłońmi"
    ),
    "Isometric_Neck_Exercise_-_Sides": (
        "izometria szyi na boki, wzmacnianie szyi, napinanie szyi w bok"
    ),
    "Chin_To_Chest_Stretch": (
        "przyciąganie brody do klatki, rozciąganie karku, rozciąganie szyi w przód"
    ),
    "Side_Neck_Stretch": "rozciąganie szyi w bok, skłon głowy w bok, rozciąganie karku",
    "Clean_Deadlift": "martwy ciąg do zarzutu, clean deadlift, martwy ciąg zarzutowy",
    "Clean_Shrug": "szrugsy do zarzutu, clean shrug, dynamiczne szrugsy",
}
