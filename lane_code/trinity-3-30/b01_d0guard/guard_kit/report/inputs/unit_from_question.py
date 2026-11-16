"""Asked unit of a dev-S1 distance or room question, parsed from the question text alone.

parse_unit(question, question_type) -> dict with keys
  unit      one of "meters", "centimeters", "feet", "inches" (distance) or
            "square meters", "square feet" (room), or None
  status    "ok"        exactly one supported unit named
            "none"      the text names no unit
            "multiple"  the text names two or more distinct units
            "unsupported" the text names exactly one unit that is not allowed for the type
                        (e.g. millimetres, yards, a linear unit in a room question)
  mentions  the distinct canonical units found, in order of first appearance

No guessing: anything other than status "ok" has unit None, and such an item is excluded from
the metre set. Ambiguous abbreviations ("m", "in") are never read as units: "in" is almost always
the preposition ("in meters"), and a bare "m" is not used by any dev-S1 question; a question that
names its unit only that way gets status "none" and is listed, not guessed.
Standard library only; Python 3.6+.
"""
import re

DISTANCE_TYPE = "object_abs_distance"
ROOM_TYPE = "room_size_estimation"

DISTANCE_UNITS = ("meters", "centimeters", "feet", "inches")
ROOM_UNITS = ("square meters", "square feet")
METRE_UNIT = {DISTANCE_TYPE: "meters", ROOM_TYPE: "square meters"}

# Area units first: they are matched and masked before linear units, so "square meters" is not
# also counted as "meters".
_AREA = [
    ("square meters", r"\bsquare\s+(?:meters?|metres?)\b|\bsq\.?\s*(?:m|meters?|metres?)\b(?!\w)|\bm\s*(?:\^\s*2|²)"),
    ("square feet", r"\bsquare\s+(?:feet|foot)\b|\bsq\.?\s*(?:ft|feet|foot)\b\.?|\bft\s*(?:\^\s*2|²)"),
    ("square centimeters", r"\bsquare\s+(?:centimeters?|centimetres?)\b|\bcm\s*(?:\^\s*2|²)"),
    ("square inches", r"\bsquare\s+inch(?:es)?\b"),
    ("square yards", r"\bsquare\s+yards?\b"),
]
_LINEAR = [
    ("centimeters", r"\b(?:centimeters?|centimetres?|cm)\b"),
    ("millimeters", r"\b(?:millimeters?|millimetres?|mm)\b"),
    ("kilometers", r"\b(?:kilometers?|kilometres?|km)\b"),
    ("meters", r"\b(?:meters?|metres?)\b"),
    ("feet", r"\b(?:feet|foot|ft)\b"),
    ("inches", r"\b(?:inch|inches)\b"),
    ("yards", r"\b(?:yards?|yd)\b"),
    ("miles", r"\bmiles?\b"),
]
_AREA_RE = [(u, re.compile(p, re.IGNORECASE)) for u, p in _AREA]
_LINEAR_RE = [(u, re.compile(p, re.IGNORECASE)) for u, p in _LINEAR]


def find_units(question):
    """Distinct canonical units named in the text, in order of first appearance."""
    text = question
    hits = []  # (position, unit)
    for unit, rx in _AREA_RE:
        for m in rx.finditer(text):
            hits.append((m.start(), unit))
        text = rx.sub(lambda m: " " * len(m.group(0)), text)  # mask, keep positions
    for unit, rx in _LINEAR_RE:
        for m in rx.finditer(text):
            hits.append((m.start(), unit))
    out = []
    for _, unit in sorted(hits):
        if unit not in out:
            out.append(unit)
    return out


def parse_unit(question, question_type):
    if question_type == DISTANCE_TYPE:
        allowed = DISTANCE_UNITS
    elif question_type == ROOM_TYPE:
        allowed = ROOM_UNITS
    else:
        raise ValueError("unsupported question_type %r" % (question_type,))
    mentions = find_units(question)
    if not mentions:
        return {"unit": None, "status": "none", "mentions": mentions}
    if len(mentions) > 1:
        return {"unit": None, "status": "multiple", "mentions": mentions}
    if mentions[0] not in allowed:
        return {"unit": None, "status": "unsupported", "mentions": mentions}
    return {"unit": mentions[0], "status": "ok", "mentions": mentions}


def is_metre(parsed, question_type):
    return parsed["status"] == "ok" and parsed["unit"] == METRE_UNIT[question_type]


if __name__ == "__main__":
    import json
    import sys
    for line in sys.stdin:
        if line.strip():
            row = json.loads(line)
            p = parse_unit(row["question"], row["question_type"])
            print(json.dumps({"id": row.get("id"), "unit": p["unit"], "status": p["status"]}, sort_keys=True))
