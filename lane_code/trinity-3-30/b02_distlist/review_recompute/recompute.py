import hashlib
import json
import re
from collections import Counter
from pathlib import Path

INPUT = Path("TASKS.jsonl")
OUTPUT = Path("RECOMPUTED_DISTANCE_LIST_150.jsonl")
REPORT = Path("RECOMPUTE_REPORT.md")
INPUT_HASH = "a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e"
EXPECTED_HASH = "028273ec3bfd1d3cd2d64f15c0fdab10fd8f905beb49fe09c3aa822a491a702e"

raw = INPUT.read_bytes()
input_hash = hashlib.sha256(raw).hexdigest()
if input_hash != INPUT_HASH:
    raise ValueError(f"Input SHA-256 mismatch: {input_hash}")
rows = [json.loads(line) for line in raw.splitlines()]
if len(rows) != 1525:
    raise ValueError(f"Expected 1525 rows, got {len(rows)}")

distance_patterns = {
    "meters": r"\b(?:meters?|metres?)\b",
    "centimeters": r"\b(?:centimeters?|centimetres?|cm)\b",
    "feet": r"\b(?:foot|feet|ft)\b",
    "inches": r"\b(?:inch|inches)\b",
}
area_patterns = {
    "square meters": r"\bsquare\s+(?:meters?|metres?)\b",
    "square feet": r"\bsquare\s+(?:foot|feet|ft)\b",
}

def classify(question, patterns):
    found = [unit for unit, pattern in patterns.items()
             if re.search(pattern, question, re.IGNORECASE)]
    if len(found) == 1:
        return found[0], "ok"
    return None, "none" if not found else "multiple"

distance = sorted((r for r in rows if r["question_type"] == "object_abs_distance"),
                  key=lambda r: r["id"])
room = sorted((r for r in rows if r["question_type"] == "room_size_estimation"),
              key=lambda r: r["id"])
if len(distance) != 150 or len(room) != 36:
    raise ValueError(f"Unexpected row counts: distance={len(distance)}, room={len(room)}")

distance_units, distance_status = Counter(), Counter()
room_units, room_status = Counter(), Counter()
exceptions = []
lines = []
for row in distance:
    unit, status = classify(row["question"], distance_patterns)
    distance_units[unit] += 1
    distance_status[status] += 1
    if status != "ok":
        exceptions.append(("distance", row["id"], status, row["question"]))
    obj = {"capture": row["native"], "metre": unit == "meters",
           "question_id": row["id"], "room": row["room"], "unit": unit,
           "unit_status": status}
    lines.append(json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(", ", ": ")) + "\n")
for row in room:
    unit, status = classify(row["question"], area_patterns)
    room_units[unit] += 1
    room_status[status] += 1
    if status != "ok":
        exceptions.append(("room", row["id"], status, row["question"]))

output_bytes = "".join(lines).encode("ascii")
output_hash = hashlib.sha256(output_bytes).hexdigest()
distance_expected = {"meters": 43, "centimeters": 28, "feet": 46, "inches": 33}
room_expected = {"square meters": 29, "square feet": 7}

def comparison(counts, expected):
    differences = [f"{unit}: {counts[unit]} vs {value}" for unit, value in expected.items()
                   if counts[unit] != value]
    if counts[None]:
        differences.append(f"null: {counts[None]} vs 0")
    return "match" if not differences else "difference: " + "; ".join(differences)

def counts_text(counts, labels):
    return ", ".join(f"{label}: {counts[key]}" for key, label in labels)

report = [
    "# Independent recompute report",
    f"TASKS.jsonl SHA-256: `{input_hash}`",
    f"RECOMPUTED_DISTANCE_LIST_150.jsonl SHA-256: `{output_hash}`",
    f"Expected output SHA-256: {'match' if output_hash == EXPECTED_HASH else 'difference'} (expected `{EXPECTED_HASH}`).",
    "Distance units: " + counts_text(distance_units, [(u, u) for u in distance_expected] + [(None, "null")]) + ".",
    "Distance statuses: " + counts_text(distance_status, [(s, s) for s in ("ok", "none", "multiple")]) + ".",
    "Distance expected counts: " + comparison(distance_units, distance_expected) + ".",
    "Room units: " + counts_text(room_units, [(u, u) for u in room_expected] + [(None, "null")]) + ".",
    "Room statuses: " + counts_text(room_status, [(s, s) for s in ("ok", "none", "multiple")]) + ".",
    "Room expected counts: " + comparison(room_units, room_expected) + ".",
    "Non-ok rows: " + ("none." if not exceptions else "listed below."),
]
for kind, row_id, status, question in exceptions:
    report.append(f"- {kind} {json.dumps(row_id, ensure_ascii=True)} ({status}): {json.dumps(question, ensure_ascii=True)}")
if len(report) > 25:
    raise ValueError("Cannot list all non-ok rows within the 25-line report limit")
OUTPUT.write_bytes(output_bytes)
REPORT.write_text("\n".join(report) + "\n", encoding="ascii", newline="\n")
print("\n".join(report))
