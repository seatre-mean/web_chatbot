"""
nlp_utils.py
------------
Text preprocessing utilities built on NLTK.

Pipeline: lowercase -> tokenize -> remove punctuation/stopwords -> lemmatize

If NLTK or its required corpora aren't available (e.g. no internet access
to download them), this module transparently falls back to a pure-Python
implementation so the chatbot still runs.
"""

import re
import string

# ---------------------------------------------------------------------------
# Try to set up NLTK. Fall back to plain Python if unavailable.
# ---------------------------------------------------------------------------
NLTK_AVAILABLE = False

try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize

    # These resources must be downloaded once (see README / setup instructions).
    # We try a lookup; if it fails we attempt a download; if that also fails
    # (no internet), we drop down to the fallback path below.
    required = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for path, name in required:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception:
                pass

    # Confirm everything actually works end-to-end before committing to NLTK.
    _lemmatizer = WordNetLemmatizer()
    _stop_words = set(stopwords.words("english"))
    _ = word_tokenize("test sentence")
    _ = _lemmatizer.lemmatize("running", pos="v")

    NLTK_AVAILABLE = True

except Exception:
    NLTK_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fallback (pure Python) setup — used only if NLTK path above failed.
# ---------------------------------------------------------------------------
_FALLBACK_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "i", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "his", "its", "our", "their", "this", "that",
    "these", "those", "am", "to", "of",
    "in", "on", "at", "for", "with", "about", "as", "by", "and", "or",
    "but", "if", "so", "than", "too", "very", "will", "just",
}

# Minimal irregular-verb + simple suffix-stripping "lemmatizer" fallback.
_IRREGULAR = {
    "is": "be", "are": "be", "was": "be", "were": "be", "am": "be",
    "has": "have", "had": "have", "having": "have",
}


def _fallback_lemmatize(word: str) -> str:
    if word in _IRREGULAR:
        return _IRREGULAR[word]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 3:
        return word[:-2]
    if word.endswith("ing") and len(word) > 5:
        return word[:-3]
    if word.endswith("ed") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def _fallback_tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text.split()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def preprocess(text: str) -> str:
    """
    Clean and normalize a piece of text for matching:
    lowercase -> tokenize -> drop punctuation/stopwords -> lemmatize.
    Returns a single space-joined string of processed tokens.
    """
    if not text:
        return ""

    if NLTK_AVAILABLE:
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t not in _stop_words and t.isalpha()]
        tokens = [_lemmatizer.lemmatize(t, pos="v") for t in tokens]
        tokens = [_lemmatizer.lemmatize(t, pos="n") for t in tokens]
        return " ".join(tokens)
    else:
        tokens = _fallback_tokenize(text)
        tokens = [t for t in tokens if t not in _FALLBACK_STOPWORDS and t.isalpha()]
        tokens = [_fallback_lemmatize(t) for t in tokens]
        return " ".join(tokens)


def using_nltk() -> bool:
    """Report which backend is active (useful for diagnostics / README demo)."""
    return NLTK_AVAILABLE
