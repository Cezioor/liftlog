"""Text normalisation for exercise search. No model imports, so models can use it too."""

import re
import unicodedata


def normalize(text):
    """Lowercase, strip Polish (and other) diacritics, unify separators.

    "Zgięcia ramion" -> "zgiecia ramion", "Łydki" -> "lydki", "Pull-up" -> "pull up".
    """
    # "ł" has no Unicode decomposition, so NFKD alone would keep it.
    text = (text or "").lower().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[-_/,;.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Polish endings cut off to compare words by their stem, longest first among those that
# share a letter ("ego" before "o"). "owego" is left out on purpose: it would cut
# "podkolanowego" to "podkolan" instead of "podkolanow" (= "podkolanowy").
POLISH_ENDINGS = ("ego", "emu", "ych", "ymi", "ami", "ach", "ow", "om", "ej", "ie", "ia", "iu",
                  "y", "e", "a", "u", "i", "o")  # fmt: skip


def polish_stem(word):
    """A normalized Polish word without its ending, for comparing forms of one word:
    "czworogłowy" / "czworogłowe" / "czworogłowych" -> "czworoglow", "dołu" -> "dol".

    Crude on purpose: it is only used to find words inside exercise names, where a
    shorter stem just finds a few more names. Short words (< 4 letters) stay as they are.
    """
    if len(word) < 4:
        return word
    for ending in POLISH_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word
