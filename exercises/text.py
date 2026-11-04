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
