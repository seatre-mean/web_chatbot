"""
skills.py
---------
"Skill" handlers for query types that need a COMPUTED answer rather than a
fixed canned response. Each skill:
  1. has a `matches(text)` function that checks if it should handle the query
  2. has a `run(text)` function that returns the answer string

These run BEFORE the intent-matching engine, so things like "what is 12*7"
or "convert 5 km to miles" get a real computed answer instead of falling
back to "I don't understand."
"""

import re
import math
import datetime


# ---------------------------------------------------------------------------
# Skill: Calculator
# ---------------------------------------------------------------------------
_MATH_TRIGGER = re.compile(
    r"(what is|what's|calculate|compute|solve|evaluate)?\s*"
    r"[-+]?\d+(\.\d+)?\s*([\+\-\*\/x\^%]|plus|minus|times|divided by|multiplied by|over)\s*[-+]?\d+(\.\d+)?",
    re.IGNORECASE,
)

_WORD_TO_OP = {
    "plus": "+", "minus": "-", "times": "*", "multiplied by": "*",
    "divided by": "/", "over": "/", "x": "*", "^": "**",
}


def _math_matches(text: str) -> bool:
    return bool(_MATH_TRIGGER.search(text))


def _math_run(text: str):
    expr = text.lower()
    # strip leading question words
    expr = re.sub(r"^(what is|what's|calculate|compute|solve|evaluate)\s*", "", expr).strip()
    expr = expr.rstrip("?").strip()

    # replace word operators with symbols (longest phrases first)
    for word, sym in sorted(_WORD_TO_OP.items(), key=lambda kv: -len(kv[0])):
        expr = expr.replace(word, f" {sym} ")

    # keep only safe characters
    cleaned = re.sub(r"[^0-9\.\+\-\*\/\(\)\s%]", "", expr)
    if not re.search(r"\d", cleaned):
        return None

    try:
        # guard against empty/garbage expressions
        if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s%]+", cleaned):
            return None
        result = eval(cleaned, {"__builtins__": {}}, {})
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{expr.strip()} = {result}"
    except ZeroDivisionError:
        return "That involves dividing by zero, which isn't defined."
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Skill: Date & Time
# ---------------------------------------------------------------------------
_DATE_PATTERNS = [
    "what is today's date", "what's today's date", "today's date",
    "what is the date", "what's the date", "current date",
]
_TIME_PATTERNS = [
    "what time is it", "what is the time", "what's the time", "current time",
]
_DAY_PATTERNS = [
    "what day is it", "what day is today", "what's the day today",
]


def _datetime_matches(text: str) -> bool:
    t = text.lower().strip().rstrip("?")
    return any(p in t for p in _DATE_PATTERNS + _TIME_PATTERNS + _DAY_PATTERNS)


def _datetime_run(text: str):
    t = text.lower().strip().rstrip("?")
    now = datetime.datetime.now()
    if any(p in t for p in _TIME_PATTERNS):
        return f"My system clock shows {now.strftime('%I:%M %p')} (server time)."
    if any(p in t for p in _DAY_PATTERNS):
        return f"Today is {now.strftime('%A')}."
    if any(p in t for p in _DATE_PATTERNS):
        return f"Today's date is {now.strftime('%B %d, %Y')}."
    return None


# ---------------------------------------------------------------------------
# Skill: Unit conversion (a small, common set)
# ---------------------------------------------------------------------------
_CONVERSIONS = {
    ("km", "miles"): lambda v: v * 0.621371,
    ("miles", "km"): lambda v: v / 0.621371,
    ("kg", "lbs"): lambda v: v * 2.20462,
    ("lbs", "kg"): lambda v: v / 2.20462,
    ("kg", "pounds"): lambda v: v * 2.20462,
    ("pounds", "kg"): lambda v: v / 2.20462,
    ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
    ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
    ("c", "f"): lambda v: v * 9 / 5 + 32,
    ("f", "c"): lambda v: (v - 32) * 5 / 9,
    ("meters", "feet"): lambda v: v * 3.28084,
    ("feet", "meters"): lambda v: v / 3.28084,
    ("inches", "cm"): lambda v: v * 2.54,
    ("cm", "inches"): lambda v: v / 2.54,
}

_CONVERT_RE = re.compile(
    r"convert\s+([\d\.]+)\s*([a-zA-Z]+)\s+(?:to|into)\s+([a-zA-Z]+)|"
    r"([\d\.]+)\s*([a-zA-Z]+)\s+(?:to|in)\s+([a-zA-Z]+)",
    re.IGNORECASE,
)


def _convert_matches(text: str) -> bool:
    return bool(_CONVERT_RE.search(text.lower()))


def _convert_run(text: str):
    m = _CONVERT_RE.search(text.lower())
    if not m:
        return None
    groups = m.groups()
    if groups[0]:
        value, from_unit, to_unit = groups[0], groups[1], groups[2]
    else:
        value, from_unit, to_unit = groups[3], groups[4], groups[5]

    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    def _variants(u):
        v = {u}
        if u.endswith("s"):
            v.add(u[:-1])
        else:
            v.add(u + "s")
        return v

    fn = None
    chosen_from, chosen_to = from_unit, to_unit
    for fu in _variants(from_unit):
        for tu in _variants(to_unit):
            if (fu, tu) in _CONVERSIONS:
                fn = _CONVERSIONS[(fu, tu)]
                chosen_from, chosen_to = fu, tu
                break
        if fn:
            break
    if fn is None:
        return None

    try:
        value = float(value)
        result = fn(value)
        return f"{value:g} {from_unit} is approximately {result:.2f} {to_unit}."
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Skill: Simple general-knowledge facts (offline mini-dictionary)
# ---------------------------------------------------------------------------
_FACTS = {
    "capital of france": "The capital of France is Paris.",
    "capital of india": "The capital of India is New Delhi.",
    "capital of usa": "The capital of the United States is Washington, D.C.",
    "capital of united states": "The capital of the United States is Washington, D.C.",
    "capital of japan": "The capital of Japan is Tokyo.",
    "capital of uk": "The capital of the United Kingdom is London.",
    "capital of united kingdom": "The capital of the United Kingdom is London.",
    "capital of germany": "The capital of Germany is Berlin.",
    "capital of italy": "The capital of Italy is Rome.",
    "capital of china": "The capital of China is Beijing.",
    "capital of russia": "The capital of Russia is Moscow.",
    "capital of canada": "The capital of Canada is Ottawa.",
    "capital of australia": "The capital of Australia is Canberra.",
    "largest planet": "Jupiter is the largest planet in our solar system.",
    "smallest planet": "Mercury is the smallest planet in our solar system.",
    "largest ocean": "The Pacific Ocean is the largest ocean on Earth.",
    "largest country": "Russia is the largest country in the world by area.",
    "tallest mountain": "Mount Everest is the tallest mountain above sea level.",
    "speed of light": "The speed of light is approximately 299,792 kilometers per second.",
    "boiling point of water": "Water boils at 100°C (212°F) at sea level.",
    "freezing point of water": "Water freezes at 0°C (32°F) at sea level.",
    "number of continents": "There are 7 continents: Asia, Africa, North America, South America, Antarctica, Europe, and Australia.",
    "number of planets": "There are 8 planets in our solar system.",
}


def _facts_matches(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in _FACTS)


def _facts_run(text: str):
    t = text.lower()
    for k, v in _FACTS.items():
        if k in t:
            return v
    return None


# ---------------------------------------------------------------------------
# Public registry — order matters (more specific skills first)
# ---------------------------------------------------------------------------
SKILLS = [
    ("facts", _facts_matches, _facts_run),
    ("convert", _convert_matches, _convert_run),
    ("datetime", _datetime_matches, _datetime_run),
    ("math", _math_matches, _math_run),
]


def try_skills(text: str):
    """
    Try each skill in order. Returns (answer, skill_name) for the first
    skill that both matches AND produces a non-None answer.
    Returns (None, None) if no skill applies.
    """
    for name, matcher, runner in SKILLS:
        if matcher(text):
            result = runner(text)
            if result:
                return result, name
    return None, None
