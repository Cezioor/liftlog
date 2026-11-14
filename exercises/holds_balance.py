"""Built-in isometric holds and balance exercises that free-exercise-db lacks.

Reviewed by the owner in two batches (2026-11-13): holds measured in time are named
"utrzymanie …" in Polish (not "… z pauzą", which is a rep exercise with a pause), and
none of them repeats an exercise already in the library. Added to
seed_data.EXTRA_EXERCISES, so `seed_exercises` creates or updates them.

A hold whose equipment is a weight (barbell, dumbbell, cable…) is a loaded hold: its
progression adds weight once every hold reaches the top of the plan's time range.
"""

HOLDS_AND_BALANCE = [
    # --- izometria_partia_1
    {
        "name": "Bodyweight Squat Hold",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "quadriceps",
        ],
        "secondary_muscles": [
            "glutes",
            "adductors",
        ],
        "aliases": ("utrzymanie przysiadu, izometria przysiadu, przysiad statyczny, squat hold"),
        "instructions": [
            (
                "Stand with your feet shoulder-width apart and squat down until "
                "your thighs are about parallel to the floor."
            ),
            (
                "Keep your chest up, your weight over the middle of the feet and"
                " your knees in line with your toes."
            ),
            (
                "Hold, breathing steadily. Easier: hold higher, or hold on to a "
                "rack. Harder: go lower or hold a weight at your chest."
            ),
        ],
    },
    {
        "name": "Split Squat Hold",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "quadriceps",
        ],
        "secondary_muscles": [
            "glutes",
        ],
        "aliases": ("utrzymanie wykroku, izometria wykroku, wykrok statyczny, split squat hold"),
        "instructions": [
            "Step one foot forward into a split stance.",
            (
                "Lower until the front thigh is about parallel to the floor and "
                "the back knee hovers just above it."
            ),
            (
                "Keep your torso upright and hold, then switch legs. Easier: "
                "stay higher or hold on to something. Harder: hold dumbbells or "
                "raise the back foot on a bench."
            ),
        ],
    },
    {
        "name": "Glute Bridge Hold",
        "muscle_group": "glutes",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "glutes",
        ],
        "secondary_muscles": [
            "hamstrings",
        ],
        "aliases": (
            "utrzymanie mostka biodrowego, izometria mostka, mostek statyczny, glute bridge hold"
        ),
        "instructions": [
            ("Lie on your back with your knees bent and feet flat on the floor, hip-width apart."),
            (
                "Squeeze your glutes and lift your hips until your body forms a "
                "straight line from shoulders to knees."
            ),
            (
                "Hold without arching your lower back. Harder: place a weight on"
                " your hips or move your feet farther away."
            ),
        ],
    },
    {
        "name": "Single-Leg Glute Bridge Hold",
        "muscle_group": "glutes",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "glutes",
        ],
        "secondary_muscles": [
            "hamstrings",
        ],
        "aliases": (
            "utrzymanie mostka biodrowego jednonóż, mostek jednonóż statyczny, "
            "izometria mostka na jednej nodze"
        ),
        "instructions": [
            ("Lie on your back with your knees bent and feet flat on the floor."),
            (
                "Straighten one leg, then push through the other heel and lift "
                "your hips until they are level."
            ),
            (
                "Hold without letting the hips drop or rotate, then switch legs."
                " Easier: keep both feet down and only shift your weight to one."
            ),
        ],
    },
    {
        "name": "Barbell Hip Thrust Hold",
        "muscle_group": "glutes",
        "equipment": "barbell",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "intermediate",
        "primary_muscles": [
            "glutes",
        ],
        "secondary_muscles": [
            "hamstrings",
        ],
        "aliases": (
            "utrzymanie hip thrusta ze sztangą, izometria hip thrusta, hip "
            "thrust statyczny, wypychanie bioder z utrzymaniem"
        ),
        "instructions": [
            ("Sit with your upper back against a bench and roll a padded barbell over your hips."),
            (
                "Drive through your heels and lift your hips until your body is "
                "level from shoulders to knees, chin slightly tucked."
            ),
            (
                "Hold at the top with your glutes squeezed and ribs down. Start "
                "lighter than for normal hip thrusts."
            ),
        ],
    },
    {
        "name": "Single-Leg Calf Raise Hold",
        "muscle_group": "calves",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "calves",
        ],
        "secondary_muscles": [],
        "aliases": (
            "utrzymanie wspięcia na palce jednonóż, izometria łydki, wspięcie "
            "statyczne, calf raise hold"
        ),
        "instructions": [
            "Stand on one foot, lightly holding a wall or rack for balance.",
            "Rise onto the ball of the foot as high as you can.",
            (
                "Hold at the top without rolling the ankle out, then switch "
                "feet. Easier: use both feet. Harder: stand on a step or hold a "
                "dumbbell."
            ),
        ],
    },
    {
        "name": "Standing Knee Raise Hold",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "quadriceps",
        ],
        "secondary_muscles": [
            "abdominals",
        ],
        "aliases": (
            "utrzymanie uniesionego kolana stojąc, izometria zginaczy biodra, "
            "uniesione kolano statycznie, knee raise hold"
        ),
        "instructions": [
            "Stand tall next to a wall for balance.",
            "Lift one knee above hip height without leaning back.",
            ("Hold, then switch legs. Harder: add an ankle weight or a band around the feet."),
        ],
    },
    {
        "name": "Adductor Ball Squeeze",
        "muscle_group": "glutes",
        "equipment": "other",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "adductors",
        ],
        "secondary_muscles": [],
        "aliases": (
            "ściskanie piłki kolanami, izometria przywodzicieli, ściskanie piłki"
            " między kolanami, adductor squeeze"
        ),
        "instructions": [
            (
                "Lie on your back with your knees bent and a ball or folded "
                "pillow between your knees."
            ),
            "Squeeze the knees together firmly without lifting your hips.",
            (
                "Hold the squeeze, then relax. Harder: do it in a glute bridge, "
                "or with straighter legs."
            ),
        ],
    },
    {
        "name": "High Plank",
        "muscle_group": "core",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "abdominals",
        ],
        "secondary_muscles": [
            "shoulders",
            "chest",
        ],
        "aliases": (
            "deska na prostych rękach, utrzymanie pompki na górze, podpór "
            "przodem na dłoniach, high plank, deska na dłoniach"
        ),
        "instructions": [
            (
                "Get into the top of a push-up: hands under your shoulders, arms"
                " straight, feet together."
            ),
            (
                "Brace your abs and squeeze your glutes so your body forms a "
                "straight line from head to heels."
            ),
            (
                "Hold without letting the hips sag or rise. Easier: knees on the"
                " floor. Harder: lift one foot or one hand."
            ),
        ],
    },
    {
        "name": "Reverse Plank",
        "muscle_group": "back",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "glutes",
            "lower back",
        ],
        "secondary_muscles": [
            "hamstrings",
            "shoulders",
        ],
        "aliases": "deska tyłem, podpór tyłem, odwrócona deska, reverse plank",
        "instructions": [
            (
                "Sit with your legs straight and your hands on the floor behind "
                "your hips, fingers towards your feet."
            ),
            (
                "Push through your hands and heels and lift your hips until your"
                " body forms a straight line."
            ),
            (
                "Hold with your shoulders away from your ears. Easier: bend your"
                " knees (tabletop). Harder: lift one leg."
            ),
        ],
    },
    {
        "name": "Bear Plank Hold",
        "muscle_group": "core",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "abdominals",
        ],
        "secondary_muscles": [
            "shoulders",
            "quadriceps",
        ],
        "aliases": (
            "utrzymanie pozycji niedźwiedzia, niedźwiedź statyczny, kolana nad ziemią, bear hold"
        ),
        "instructions": [
            ("Kneel on all fours with your hands under your shoulders and knees under your hips."),
            ("Tuck your toes and lift your knees a few centimetres off the floor, back flat."),
            ("Hold while breathing steadily. Harder: lift one hand or the opposite hand and foot."),
        ],
    },
    {
        "name": "L-Sit",
        "muscle_group": "core",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "expert",
        "primary_muscles": [
            "abdominals",
        ],
        "secondary_muscles": [
            "triceps",
            "quadriceps",
        ],
        "aliases": "L-sit, utrzymanie siadu L, siad prosty w podporze, l sit",
        "instructions": [
            (
                "Sit between parallettes or dip bars (or on the floor) and place"
                " your hands beside your hips."
            ),
            (
                "Press down with straight arms and lift your body and your "
                "straight legs until they are parallel to the floor."
            ),
            (
                "Hold with your shoulders pushed down. Easier: tuck your knees "
                "to your chest (tuck sit), or keep one leg bent."
            ),
        ],
    },
    {
        "name": "Back Extension Hold",
        "muscle_group": "back",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "lower back",
        ],
        "secondary_muscles": [
            "glutes",
            "hamstrings",
        ],
        "aliases": (
            "utrzymanie wyprostu na ławce rzymskiej, izometria prostowników, "
            "wyprost statyczny, back extension hold"
        ),
        "instructions": [
            ("Set up on a back extension (Roman chair) bench with the pad just below your hips."),
            ("Raise your torso until your body forms a straight line, without arching past it."),
            ("Hold with your glutes squeezed. Harder: hold a weight plate at your chest."),
        ],
    },
    {
        "name": "Pallof Press Hold",
        "muscle_group": "core",
        "equipment": "cable",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "abdominals",
        ],
        "secondary_muscles": [],
        "aliases": (
            "utrzymanie wyciskania pallofa, izometria antyrotacji, pallof hold, "
            "antyrotacja statyczna"
        ),
        "instructions": [
            (
                "Set a cable at chest height and stand side-on to it, holding "
                "the handle at your chest with both hands."
            ),
            (
                "Step away until you feel the pull, then press the handle "
                "straight out in front of your chest."
            ),
            (
                "Hold without letting your torso turn towards the cable, then "
                "switch sides. Also works with a band."
            ),
        ],
    },
    {
        "name": "Bird Dog",
        "muscle_group": "back",
        "equipment": "bodyweight",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "lower back",
        ],
        "secondary_muscles": [
            "glutes",
            "abdominals",
        ],
        "aliases": ("bird dog, pies myśliwski, przeciwstawne unoszenie ręki i nogi w klęku"),
        "instructions": [
            (
                "Kneel on all fours with your hands under your shoulders and "
                "knees under your hips, back flat."
            ),
            (
                "Slowly reach one arm forward and the opposite leg back until "
                "both are in line with your body."
            ),
            (
                "Pause for a moment without tilting your hips, return, and "
                "repeat on the other side. Harder: hold each rep longer or add a"
                " band."
            ),
        ],
    },
    {
        "name": "Push-Up Bottom Hold",
        "muscle_group": "chest",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "intermediate",
        "primary_muscles": [
            "chest",
        ],
        "secondary_muscles": [
            "triceps",
            "shoulders",
        ],
        "aliases": ("utrzymanie pompki na dole, izometria pompki, pompka statyczna, push up hold"),
        "instructions": [
            "Start in a push-up position with your body in a straight line.",
            (
                "Lower until your chest is a few centimetres above the floor, "
                "elbows at about 45° to your body."
            ),
            ("Hold without letting your hips sag. Easier: knees on the floor or hands on a bench."),
        ],
    },
    {
        "name": "Chin-Up Hold",
        "muscle_group": "back",
        "equipment": "pullup_bar",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "lats",
        ],
        "secondary_muscles": [
            "biceps",
            "forearms",
        ],
        "aliases": (
            "utrzymanie brody nad drążkiem, zwis na ugiętych rękach, izometria "
            "podciągania, flexed arm hang, chin up hold"
        ),
        "instructions": [
            "Grab a pull-up bar with an underhand, shoulder-width grip.",
            "Jump or step up so your chin is above the bar.",
            (
                "Hold with your shoulders down and chest towards the bar, then "
                "lower slowly. A step towards your first pull-up. Harder: hold "
                "with a weight belt."
            ),
        ],
    },
    {
        "name": "Inverted Row Hold",
        "muscle_group": "back",
        "equipment": "other",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "middle back",
        ],
        "secondary_muscles": [
            "lats",
            "biceps",
        ],
        "aliases": (
            "utrzymanie podciągania australijskiego, izometria wiosłowania, "
            "australijskie statycznie, inverted row hold"
        ),
        "instructions": [
            (
                "Set a bar in a rack at about waist height and hang under it "
                "with straight arms, heels on the floor."
            ),
            "Pull your chest to the bar with your body in a straight line.",
            (
                "Hold at the top with your shoulder blades squeezed. Easier: "
                "raise the bar or bend your knees. Harder: lower the bar or "
                "raise your feet."
            ),
        ],
    },
    {
        "name": "Dip Support Hold",
        "muscle_group": "triceps",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "triceps",
        ],
        "secondary_muscles": [
            "chest",
            "shoulders",
        ],
        "aliases": (
            "utrzymanie podporu na poręczach, podpór na poręczach, izometria "
            "dipów, dip hold, support hold"
        ),
        "instructions": [
            "Stand between parallel bars and grab them.",
            ("Press up until your arms are straight and your feet leave the floor."),
            (
                "Hold with your shoulders pushed down and away from your ears. A"
                " step towards your first dip. Easier: let your toes touch a "
                "box."
            ),
        ],
    },
    {
        "name": "Dumbbell Curl Hold",
        "muscle_group": "biceps",
        "equipment": "dumbbell",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "biceps",
        ],
        "secondary_muscles": [
            "forearms",
        ],
        "aliases": (
            "utrzymanie uginania hantli, izometria bicepsa, uginanie statyczne "
            "pod kątem prostym, curl hold"
        ),
        "instructions": [
            "Stand holding dumbbells with an underhand grip.",
            (
                "Curl them up until your elbows are bent at 90° and your "
                "forearms are parallel to the floor."
            ),
            "Hold with your elbows by your sides and your wrists straight.",
        ],
    },
    {
        "name": "Barbell Static Hold",
        "muscle_group": "forearms",
        "equipment": "barbell",
        "measurement": "time",
        "category": "isometric",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "forearms",
        ],
        "secondary_muscles": [
            "traps",
        ],
        "aliases": (
            "utrzymanie sztangi, trzymanie sztangi na czas, izometria chwytu, "
            "static hold, siła chwytu"
        ),
        "instructions": [
            "Set a barbell on the safety pins of a rack at mid-thigh height.",
            ("Grip it with a double overhand grip and stand up with it, arms straight."),
            ("Hold as long as your grip lasts, shoulders down. Harder: no chalk or a thicker bar."),
        ],
    },
    # --- rownowaga_partia_2
    {
        "name": "Tandem Stance",
        "muscle_group": "calves",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "motor",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "calves",
        ],
        "secondary_muscles": [
            "glutes",
            "abdominals",
        ],
        "aliases": (
            "utrzymanie stania stopa za stopą, stanie w tandemie, stopa przed stopą, tandem stance"
        ),
        "instructions": [
            (
                "Stand with one foot directly in front of the other, heel "
                "touching toes, near a wall for safety."
            ),
            "Keep your hips level and your eyes on a fixed point.",
            (
                "Hold, then swap the front foot. Harder: close your eyes or turn"
                " your head slowly from side to side."
            ),
        ],
    },
    {
        "name": "Heel-to-Toe Walk",
        "muscle_group": "calves",
        "equipment": "bodyweight",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": False,
        "level": "beginner",
        "primary_muscles": [
            "calves",
        ],
        "secondary_muscles": [
            "glutes",
            "abdominals",
        ],
        "aliases": (
            "chód stopa za stopą, chód pięta-palce, chodzenie po linii, tandem "
            "walk, heel to toe walk"
        ),
        "instructions": [
            "Stand tall next to a wall or along a line on the floor.",
            ("Walk forward placing the heel of each foot right in front of the toes of the other."),
            (
                "Count steps; move slowly and keep your eyes ahead, not on your "
                "feet. Harder: walk backwards or with your eyes closed (with "
                "someone next to you)."
            ),
        ],
    },
    {
        "name": "Single-Leg Airplane Hold",
        "muscle_group": "glutes",
        "equipment": "bodyweight",
        "measurement": "time",
        "category": "motor",
        "is_unilateral": True,
        "level": "intermediate",
        "primary_muscles": [
            "glutes",
            "hamstrings",
        ],
        "secondary_muscles": [
            "lower back",
            "abdominals",
        ],
        "aliases": (
            "utrzymanie jaskółki, samolot, samolot na jednej nodze, jaskółka, "
            "waga na jednej nodze, airplane hold"
        ),
        "instructions": [
            "Stand on one leg with a slight bend in the knee.",
            (
                "Hinge forward at the hips and lift the other leg back until "
                "your torso and the lifted leg are about parallel to the floor, "
                "arms out to the sides."
            ),
            (
                "Hold with your hips level, then switch legs. Easier: lean less "
                "and keep a fingertip on a wall."
            ),
        ],
    },
    {
        "name": "Bodyweight Single-Leg Romanian Deadlift",
        "muscle_group": "hamstrings",
        "equipment": "bodyweight",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "hamstrings",
            "glutes",
        ],
        "secondary_muscles": [
            "lower back",
        ],
        "aliases": (
            "martwy ciąg na jednej nodze, bez obciążenia, rumuński jednonóż, "
            "single leg rdl, martwy ciąg jednonóż"
        ),
        "instructions": [
            ("Stand on one leg with a soft knee and your arms relaxed in front of you."),
            (
                "Hinge at the hips and reach your hands towards the floor while "
                "the other leg goes back in line with your torso."
            ),
            (
                "Return to standing by squeezing the glute of the standing leg; "
                "keep your hips square to the floor. Harder: hold a kettlebell "
                "(then it is the Kettlebell One-Legged Deadlift)."
            ),
        ],
    },
    {
        "name": "Y-Balance Reach",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "intermediate",
        "primary_muscles": [
            "quadriceps",
            "glutes",
        ],
        "secondary_muscles": [
            "calves",
            "abdominals",
        ],
        "aliases": (
            "sięganie nogą w trzech kierunkach, y-balance, sięganie stopą w "
            "literę Y, star excursion, gwiazda"
        ),
        "instructions": [
            "Stand on one leg with your hands on your hips.",
            (
                "Bend the standing knee and reach the other foot as far as you "
                "can forward, then back-right and back-left (a Y shape), tapping"
                " the floor lightly."
            ),
            (
                "One rep = all three directions; keep the standing heel down and"
                " the knee in line with the toes. Easier: reach less far."
            ),
        ],
    },
    {
        "name": "Lateral Step-Down",
        "muscle_group": "quads",
        "equipment": "other",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "quadriceps",
        ],
        "secondary_muscles": [
            "glutes",
        ],
        "aliases": (
            "schodzenie bokiem ze stopnia, step down bokiem, opuszczanie się ze "
            "stopnia, kontrola kolana"
        ),
        "instructions": [
            ("Stand side-on on a low step or box on one leg, the other foot hanging off the side."),
            (
                "Slowly bend the standing knee and lower until the free heel "
                "lightly touches the floor."
            ),
            (
                "Push back up; keep the knee in line with the second toe and the"
                " hips level. Easier: a lower step. Harder: a higher step or a "
                "slower descent."
            ),
        ],
    },
    {
        "name": "Reverse Lunge to Knee Drive Balance",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "beginner",
        "primary_muscles": [
            "quadriceps",
            "glutes",
        ],
        "secondary_muscles": [
            "abdominals",
            "calves",
        ],
        "aliases": (
            "wykrok w tył z uniesieniem kolana, z utrzymaniem równowagi, wykrok "
            "z kolanem w górę, wykrok w tył z balansem, lunge to knee drive"
        ),
        "instructions": [
            "Step back into a reverse lunge.",
            ("Push through the front foot to stand up, driving the back knee up to hip height."),
            (
                "Pause for two seconds on one leg before the next rep. Harder: "
                "rise onto the toes of the standing foot at the top."
            ),
        ],
    },
    {
        "name": "Single-Leg Band Kicks",
        "muscle_group": "glutes",
        "equipment": "band",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "intermediate",
        "primary_muscles": [
            "abductors",
            "glutes",
        ],
        "secondary_muscles": [
            "adductors",
            "calves",
        ],
        "aliases": (
            "kopnięcia z gumą stojąc jednonóż, kopnięcia z gumą na jednej nodze,"
            " odwodzenie nogi z gumą, t-band kicks, stabilizacja kolana z gumą"
        ),
        "instructions": [
            ("Loop a band around both ankles, or anchor it and loop it around one ankle."),
            (
                "Stand on one leg with a soft knee and move the other leg "
                "against the band (out to the side, forward or back) in small, "
                "controlled kicks."
            ),
            (
                "The standing leg does the balancing work: keep its knee and hip"
                " steady. Switch legs."
            ),
        ],
    },
    {
        "name": "Single-Leg Hop and Stick",
        "muscle_group": "quads",
        "equipment": "bodyweight",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "intermediate",
        "primary_muscles": [
            "quadriceps",
            "calves",
        ],
        "secondary_muscles": [
            "glutes",
        ],
        "aliases": (
            "skok jednonóż z zatrzymaniem lądowania, skok na jednej nodze z "
            "utrzymaniem lądowania, hop and stick, skok jednonóż z zatrzymaniem,"
            " lądowanie na jednej nodze"
        ),
        "instructions": [
            ("A later-stage exercise: first master the Lateral Step-Down and the Y-Balance Reach."),
            "Stand on one leg.",
            ("Hop a short distance forward (or to the side) and land softly on the same leg."),
            (
                "Freeze the landing for two to three seconds with the knee over "
                "the toes before the next hop. Easier: smaller hops. Harder: "
                "longer hops or changing direction."
            ),
        ],
    },
    {
        "name": "Bosu Ball Squat",
        "muscle_group": "quads",
        "equipment": "other",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": False,
        "level": "intermediate",
        "primary_muscles": [
            "quadriceps",
        ],
        "secondary_muscles": [
            "glutes",
            "abdominals",
        ],
        "aliases": (
            "przysiad na bosu, przysiad na piłce bosu, bosu squat, przysiad na niestabilnym podłożu"
        ),
        "instructions": [
            (
                "Place a Bosu ball dome side down (harder) or dome side up "
                "(easier) and step onto it with your feet shoulder-width apart."
            ),
            (
                "Find your balance, then squat down slowly until your thighs are"
                " about parallel to the floor."
            ),
            ("Stand back up with control. Use a rack or a partner nearby when you start."),
        ],
    },
    {
        "name": "Single-Leg Balance Ball Toss",
        "muscle_group": "calves",
        "equipment": "other",
        "measurement": "reps",
        "category": "motor",
        "is_unilateral": True,
        "level": "intermediate",
        "primary_muscles": [
            "calves",
            "glutes",
        ],
        "secondary_muscles": [
            "abdominals",
        ],
        "aliases": (
            "rzucanie piłką stojąc na jednej nodze, rzuty piłką na jednej nodze,"
            " łapanie piłki na jednej nodze, ball toss balance"
        ),
        "instructions": [
            ("Stand on one leg facing a wall or a partner, holding a light ball."),
            ("Throw the ball and catch it while keeping your balance on the standing leg."),
            ("Count catches, then switch legs. Harder: throw to the sides or stand on a cushion."),
        ],
    },
    {
        "name": "Stability Ball Kneeling Balance",
        "muscle_group": "core",
        "equipment": "other",
        "measurement": "time",
        "category": "motor",
        "is_unilateral": False,
        "level": "expert",
        "primary_muscles": [
            "abdominals",
        ],
        "secondary_muscles": [
            "glutes",
            "quadriceps",
        ],
        "aliases": (
            "utrzymanie klęku na piłce gimnastycznej, klęk na fitballu, balans "
            "na piłce w klęku, kneeling on stability ball"
        ),
        "instructions": [
            ("Put a stability ball next to a wall or rack and place your hands on top of it."),
            (
                "Carefully bring one knee and then the other onto the ball, then"
                " let go with your hands."
            ),
            (
                "Hold an upright kneeling position with your hips extended. Keep"
                " a safe area around you. Easier: keep your hands on the ball."
            ),
        ],
    },
]
