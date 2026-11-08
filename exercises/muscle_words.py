"""Muscle words for the exercise search, Polish and English, formal and colloquial.

Reviewed by the owner (2026-11-08). Each entry: the words someone may type (comma
separated; other forms of a word are found by its stem, see text.polish_stem), the
muscles they mean (the 17 muscles free-exercise-db tags exercises with, by their Polish
names below), and optional keywords: exercises with one of them in a Polish name come
first ("tylne aktony" among all shoulder exercises). For muscles the data doesn't tag
(hip flexors, tibialis) the keywords are the only way to find them.

Keywords are never body parts that a name uses for a position ("kolan" in "przyciąganie
kolan do klatki", "kark" in "sztanga na karku"). Anatomy only, no injuries or diseases
(ACL, meniscus): those belong to the rehab consultation (Stage 2).

Used by exercises.services (parse_query, search_exercises, equipment_suggestions).
"""

# The 17 muscles of free-exercise-db (Exercise.primary_muscles / secondary_muscles).
MUSCLE_NAMES = {
    "brzuch": "abdominals",
    "odwodziciele": "abductors",
    "przywodziciele": "adductors",
    "biceps": "biceps",
    "łydki": "calves",
    "klatka": "chest",
    "przedramiona": "forearms",
    "pośladki": "glutes",
    "dwugłowe": "hamstrings",
    "najszersze": "lats",
    "dół pleców": "lower back",
    "środek pleców": "middle back",
    "szyja": "neck",
    "czworogłowe": "quadriceps",
    "barki": "shoulders",
    "kaptury": "traps",
    "triceps": "triceps",
}

# (words someone may type, muscles, keywords in exercise names)
MUSCLE_WORDS = [
    # --- Duże grupy (już działają, zatwierdzone; dla porządku w jednym miejscu)
    ("pośladki, pośladek, dupa, dupę, dupka, tyłek, pupa, glutes, glute, butt", "pośladki", ""),
    (
        (
            "klata, klatka, chest, piersiowe, mięśnie piersiowe, piersiowy większy, "
            "piersiowy mniejszy, pecs"
        ),
        "klatka",
        "",
    ),
    ("plecy, grzbiet, back, lats", "najszersze, środek pleców, dół pleców", ""),
    ("barki, bark, shoulders, shoulder, delts", "barki", ""),
    ("biceps, bicki, bica, bicep", "biceps", ""),
    ("triceps, tricki, tricep", "triceps", ""),
    ("przedramiona, przedramię, forearms, forearm", "przedramiona", ""),
    ("uda, udo, czwórki, czworogłowe, quads, quad", "czworogłowe", ""),
    ("dwugłowe, dwójki, hamstringi, tył uda, hamstrings, hamstring", "dwugłowe", ""),
    ("łydki, łydka, łydy, calves, calf", "łydki", ""),
    ("nogi, legs", "czworogłowe, dwugłowe, pośladki, łydki, przywodziciele, odwodziciele", ""),
    ("brzuch, brzuszek, abs, absy, core, kaloryfer, mięśnie brzucha", "brzuch", ""),
    ("kaptury, kaptur, trapezy, traps", "kaptury", ""),
    ("ramiona, ręce, ręka, arms", "biceps, triceps, przedramiona", ""),
    # --- Nazwy anatomiczne (nowe)
    ("najszerszy grzbietu, najszerszy, najszersze, latissimus", "najszersze", ""),
    ("czworoboczny, trapezowy, mięsień czworoboczny grzbietu, trapezius", "kaptury", ""),
    ("obły większy", "najszersze", ""),
    (
        "równoległoboczny, równoległoboczne, romboidalny, rhomboids",
        "środek pleców",
        "równoległoboczn, ściąganie łopatek",
    ),
    ("środek pleców, łopatki, między łopatkami", "środek pleców", "łopatk"),
    (
        (
            "prostowniki grzbietu, prostowniki, prostownik, lędźwie, odcinek lędźwiowy, "
            "dół pleców, dolna część pleców, lower back"
        ),
        "dół pleców",
        "prostownik, lędźw",
    ),
    ("wielodzielny", "dół pleców", ""),
    (
        "kręgosłup, odcinek piersiowy, odcinek szyjny, spine, thoracic",
        "dół pleców, środek pleców, szyja",
        "kręgosłup",
    ),
    ("naramienny, naramienne, mięsień naramienny, deltoid", "barki", ""),
    ("dwugłowy ramienia, biceps ramienia", "biceps", ""),
    ("trójgłowy ramienia, trójgłowy", "triceps", ""),
    ("ramienny, ramienno-promieniowy, brachialis", "biceps, przedramiona", "ramienn, młotkow"),
    ("czworogłowy uda, czworogłowy, mięsień czworogłowy", "czworogłowe", ""),
    (
        (
            "dwugłowy uda, kulszowo-goleniowe, mięśnie kulszowo-goleniowe, półścięgnisty, "
            "półbłoniasty"
        ),
        "dwugłowe",
        "",
    ),
    ("pośladkowy wielki, pośladkowy", "pośladki", ""),
    ("pośladkowy średni, pośladkowy mały", "odwodziciele, pośladki", "odwodz"),
    ("gruszkowaty, piriformis", "pośladki", "gruszkowat"),
    (
        "przywodziciele, przywodziciel, pachwina, pachwiny, adductors, krawiecki, smukły",
        "przywodziciele",
        "",
    ),
    ("odwodziciele, odwodziciel, abductors", "odwodziciele", ""),
    (
        ("brzuchaty łydki, płaszczkowaty, ścięgno achillesa, achilles, gastrocnemius, soleus"),
        "łydki",
        "płaszczkowat, achilles",
    ),
    ("strzałkowe, mięśnie strzałkowe, peroneals", "łydki", "strzałkow"),
    ("prosty brzucha, mięsień prosty brzucha", "brzuch", ""),
    (
        "skośne brzucha, skośne, mięśnie skośne",
        "brzuch",
        "skośne brzuszki, brzuszki skośne, skręt, skłon boczn",
    ),
    ("poprzeczny brzucha", "brzuch", "vacuum, wciąganie"),
    ("mostkowo-obojczykowo-sutkowy, szyja, kark", "szyja", ""),
    ("dźwigacz łopatki, pochyłe", "szyja, kaptury", ""),
    # --- Mniejsze mięśnie, których nie ma w danych (najbliższy mięsień + słowa kluczowe)
    (
        "tylne aktony, tylny akton, tył barków, tylne barki, rear delts",
        "barki",
        "tylne aktony, odwrotne rozpiętki, face pull, przyciąganie liny do twarzy",
    ),
    (
        "przednie aktony, przód barków, przednie barki, front delts",
        "barki",
        "przednie barki, wznosy przodem",
    ),
    ("boczne aktony, boczne barki, side delts", "barki", "boczne barki, wznosy bokiem"),
    (
        (
            "stożek rotatorów, rotatory, rotator cuff, nadgrzebieniowy, podgrzebieniowy, "
            "obły mniejszy, podłopatkowy"
        ),
        "barki",
        "rotacja zewnętrzna, rotacja wewnętrzna, rotator",
    ),
    ("zębaty przedni, serratus", "klatka", "zębaty, protrakcja"),
    ("górna klatka, klatka górna", "klatka", "ławce skośnej"),
    ("dolna klatka, klatka dolna", "klatka", "skosie ujemnym, dolna klatka, poręcz"),
    (
        "dolny brzuch, dolne partie brzucha",
        "brzuch",
        "odwrotne brzuszki, unoszenie nóg, unoszenie kolan, przyciąganie kolan",
    ),
    (
        "zginacze bioder, zginacz biodra, biodrowo-lędźwiowy, hip flexors",
        "",
        "zginacz, unoszenie kolana",
    ),
    (
        "piszczelowy przedni, piszczel, przód goleni, tibialis",
        "",
        "piszczelow, unoszenie palców stóp",
    ),
    ("nadgarstki, nadgarstek, wrist", "przedramiona", "nadgarst"),
    (
        "siła chwytu, chwyt, grip",
        "przedramiona",
        "siła chwytu, chwyt szczypcowy, zwis, spacer farmera",
    ),
    # --- Okolice ciała
    ("dół podkolanowy, pod kolanem, tył kolana", "dwugłowe, łydki", ""),
    ("biodra, biodro, staw biodrowy", "pośladki, odwodziciele, przywodziciele", "biodr"),
    (
        (
            "pasmo biodrowo-piszczelowe, pasmo biodrowe, it band, itb, "
            "naprężacz powięzi szerokiej, tfl"
        ),
        "odwodziciele",
        "pasm, biodrowo-piszczel",
    ),
    ("miednica, obręcz biodrowa", "pośladki", "miednic"),
    ("staw barkowy, obręcz barkowa", "barki", ""),
    ("łokieć, łokcie, łokcia", "biceps, triceps, przedramiona", ""),
    ("kolana, kolano, rzepka, ścięgno rzepki", "czworogłowe, dwugłowe", "krążenia kolan"),
    (
        ("stopy, stopa, kostka, staw skokowy, rozcięgno podeszwowe, podeszwa, plantar fascia"),
        "łydki",
        "krążenia stóp, rolowanie stopy, krążenia kostek",
    ),
]
