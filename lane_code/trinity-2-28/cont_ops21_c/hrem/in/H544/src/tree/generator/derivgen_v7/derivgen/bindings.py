"""Bind questions with canonical parsers or parent-reviewed, question-bound plans."""
import re
from decimal import Decimal, InvalidOperation

from .common import ProvenanceError, Refusal, defer, digest

F17 = {
    "absolute_count", "relative_count", "absolute_distance_object", "relative_distance_object",
    "absolute_size_object", "relative_size_object", "relative_direction_object", "absolute_direction_object",
}

FAMILIES = {
    "object_counting", "object_abs_distance", "object_rel_distance", "object_size_estimation",
    "room_size_estimation", "object_rel_direction_easy", "object_rel_direction_medium",
    "object_rel_direction_hard", "route_planning", "obj_appearance_order", "camera_displacement",
    "camera_movement_direction", "camera_rotation", "camera_obj_abs_dist", "camera_obj_rel_dist_v1",
    "camera_obj_rel_dist_v2", "camera_obj_rel_dist_v3", "camera_obj_rel_dist", "obj_obj_relative_pos_lr",
    "obj_obj_relative_pos_nf", "obj_obj_relative_pos_ud",
}
FAMILIES |= F17
NUMERIC = {"object_counting", "object_abs_distance", "object_size_estimation", "room_size_estimation",
           "camera_displacement", "camera_obj_abs_dist", "camera_rotation", "absolute_count", "absolute_distance_object", "absolute_size_object", "absolute_direction_object"}
UNITS = {"m": (1., "m"), "cm": (100., "m"), "mm": (1000., "m"),
         "ft": (1/.3048, "m"), "inch": (1/.0254, "m"),
         "m2": (1., "m2"), "ft2": (1/.09290304, "m2"), "count": (1., "count"),
         "degree": (1., "degree")}


# Bare generic classes and dataset placeholders cannot bind an object referent.
GENERIC_LABELS = frozenset({
    "object", "objects", "furniture", "appliance", "container", "item", "items", "stuff",
    "machine", "remove", "other", "others", "other object", "other objects", "misc",
    "miscellaneous", "unknown", "unlabeled", "unlabelled", "void", "background",
    "closet wall", "shower floor", "shower walls", "window head", "window lintel", "split",
})
OBJECT_ROLES = ("cat", "a", "b", "target", "stand", "face", "query", "obj", "ref", "start", "goal")

LABEL_TYPOS = {"bathroon": "bathroom", "copmuter": "computer", "joga": "yoga",
               "cofee": "coffee", "electic": "electric"}
_TYPO = re.compile(r"\b(" + "|".join(LABEL_TYPOS) + r")\b", re.I)


def fix_label_typos(text):
    def replace(match):
        word = match[0]
        fixed = LABEL_TYPOS[word.lower()]
        return fixed.upper() if word.isupper() else fixed.capitalize() if word.istitle() else fixed
    return _TYPO.sub(replace, text)


def label_typo_fixes(row):
    si = row.get("student_input", row)
    text = " ".join([si["question"], *si.get("options", [])])
    return {word: LABEL_TYPOS[word] for word in sorted({m[0].lower() for m in _TYPO.finditer(text)})}


def normalized_reviewed(row, reviewed):
    """Check the source binding hash before applying the shared spelling map."""
    if not reviewed or not label_typo_fixes(row):
        return reviewed
    hashes = {digest(question(row, fix_typos=False)), digest(question(row))}
    if reviewed.get("question_sha256") not in hashes or reviewed.get("reviewed") is not True:
        raise ProvenanceError("structured binding is not reviewed/question-bound")
    def fixed(value):
        if isinstance(value, str): return fix_label_typos(value)
        if isinstance(value, dict): return {fix_label_typos(k): fixed(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)): return [fixed(v) for v in value]
        return value
    return {**reviewed, "question_sha256": digest(question(row)), "bindings": fixed(reviewed["bindings"])}


def is_generic_label(name):
    name = " ".join(name.lower().split())
    return (name in GENERIC_LABELS or "/" in name
            or bool(re.search(r"\b(?:remove|objects?)\b", name)))


def object_labels(plan):
    labels = [plan[k] for k in OBJECT_ROLES if k in plan]
    labels += plan.get("cands", []) + plan.get("cats", [])
    labels += [name for action, name in plan.get("plan", []) if action == "go"]
    return list(dict.fromkeys(labels))


def validate_labels(labels):
    from .plan_contract import count_noun
    normalized = [" ".join(label.lower().split()) for label in labels]
    if any(is_generic_label(label) for label in normalized):
        raise Refusal("generic_label")
    singulars = [count_noun(label) for label in normalized]
    if len(set(singulars)) != len(singulars):
        raise Refusal("same_singular_labels")


def gt_label(row):
    """Select source truth without treating an own-head prediction as GT."""
    head = row.get("head_program") or {}
    if (head.get("readout_source") or {}).get("kind") != "own_heads":
        return row["answer"]
    if "gt_answer" not in head:
        raise Refusal("own_head_row_without_gt_label")
    label = head["gt_answer"]
    if row["question_type"] in NUMERIC:
        try:
            valid = type(label) in (int, float, str) and Decimal(str(label)).is_finite()
        except InvalidOperation:
            valid = False
    else:
        options = question(row)["options"]
        letters = {m.group(1) for o in options if isinstance(o, str)
                   and (m := re.match(r"^([A-Z])\.\s*\S", o.strip()))}
        valid = isinstance(label, str) and label in letters
    if not valid:
        raise Refusal("own_head_row_invalid_gt_label")
    return label


def question(row, *, fix_typos=True):
    si = row.get("student_input", row)
    q = {"question_type": row["question_type"], "question": si["question"],
         "options": si.get("options", [])}
    if not isinstance(q["question"], str) or not q["question"].strip():
        raise Refusal("missing_question")
    # Never carry source timestamps or target rationale into model-visible text.
    if re.search(r"\b(seconds?|timestamps?|\d+:\d\d)\b", q["question"], re.I):
        raise Refusal("question_uses_seconds")
    for k in re.findall(r"\bframe\s+(\d+)", q["question"], re.I):
        if not 1 <= int(k) <= 32:
            raise Refusal("question_frame_out_of_range")
    if re.search(r"\bframe\s+0\b", q["question"], re.I):
        raise Refusal("zero_based_question_frame")
    if fix_typos:
        q["question"] = fix_label_typos(q["question"])
        q["options"] = [fix_label_typos(o) for o in q["options"]]
    return q


def bind(q, T, reviewed=None):
    t = q["question_type"]
    if t not in FAMILIES:
        raise Refusal("unknown_question_family", t)
    parsed = None
    try:
        parsed = parse_f17(q, T) if t in F17 else T.parse_vsti(q) if (t.startswith("camera_") or t.startswith("obj_obj_")) else T.parse_vsi(q)
    except (AttributeError, ValueError, IndexError, TypeError):
        pass
    if t == "object_counting" and not parsed:
        parsed = parse_f17({**q, "question_type": "absolute_count"}, T)
    if not parsed:
        from .paraphrase import parse_paraphrase
        parsed = parse_paraphrase(q, T)
    if t == "camera_rotation" and not parsed:
        frames = re.search(r"between frame (\d+) and frame (\d+) of (\d+)", q["question"], re.I)
        if frames:
            parsed = dict(zip(("i", "j", "M"), map(int, frames.groups())))
    if t == "camera_obj_rel_dist" and (not parsed or type(parsed.get("k")) is not int
            or not 1 <= parsed["k"] <= 32 or not isinstance(parsed.get("cands"), list)
            or len(parsed["cands"]) < 2 or any(not c for c in parsed["cands"])):
        defer("missing_validated_bindings", t)
    if reviewed:
        if reviewed.get("question_sha256") != digest(q) or reviewed.get("reviewed") is not True:
            raise ProvenanceError("structured binding is not reviewed/question-bound")
        plan = reviewed["bindings"]
        if parsed and any(k in plan and plan[k] != v for k, v in parsed.items()):
            raise Refusal("binding_parser_disagreement")
        parsed = {**(parsed or {}), **plan}
    if not parsed and t != "room_size_estimation":
        defer("missing_validated_bindings", t)
    parsed = parsed or {}
    if parsed.get("M", 32) != 32:
        raise Refusal("question_frame_count")
    if t == "route_planning":
        if (not parsed.get("plan") or any(s[0] not in ("go", "turn") for s in parsed["plan"])
                or not any(s[0] == "turn" for s in parsed["plan"])):
            raise Refusal("underspecified_route")
        if parsed["start"] == parsed["face"]:
            raise Refusal("ambiguous_route_start_facing")
    labels = object_labels(parsed)
    if t in ('object_rel_distance', 'relative_distance_object') or t.startswith('camera_obj_rel_dist'):
        labels = list(dict.fromkeys(labels + list(T.option_texts(q['options']).values())))
    validate_labels(labels)
    validate_plan(q, parsed, T)
    return parsed


def unit_policy(q, config, reviewed=None):
    t = q["question_type"]
    if t not in NUMERIC:
        return None
    policy = (reviewed or {}).get("display") or config.get("question_units", {}).get(t)
    if policy is None and t in F17:
        policy = {"unit": "count" if t == "absolute_count" else "degree" if t == "absolute_direction_object" else "m",
                  "decimals": 0 if t in ("absolute_count", "absolute_direction_object") else 2}
    if policy is None:
        defer("missing_question_unit_policy", t)
    u, places = policy.get("unit"), policy.get("decimals")
    if u not in UNITS or type(places) is not int or not 0 <= places <= 6:
        raise ProvenanceError("invalid display unit/precision")
    expected = "count" if t in ("object_counting", "absolute_count") else "degree" if t in ("camera_rotation", "absolute_direction_object") else "m2" if t == "room_size_estimation" else "m"
    if UNITS[u][1] != expected:
        raise Refusal("question_unit_dimension")
    if t in F17 and (u != expected or places != (0 if expected in ("count", "degree") else 2)):
        raise Refusal("f17_unit_precision_mismatch")
    text = q["question"].lower()
    mentions = []
    for unit, pattern in {"m2": r"square (?:met[er]{2}s?)|m²", "ft2": r"square (?:feet|foot)|ft²",
                          "cm": r"centimet[er]{2}s?|\bcm\b", "mm": r"millimet[er]{2}s?|\bmm\b",
                          "inch": r"inches|\binch\b", "ft": r"\bfeet\b|\bfoot\b",
                          "m": r"\bmet[er]{2}s?\b", "degree": r"\bdegrees?\b"}.items():
        if re.search(pattern, text): mentions.append(unit)
    if "m2" in mentions: mentions = [x for x in mentions if x != "m"]
    if "ft2" in mentions: mentions = [x for x in mentions if x != "ft"]
    if mentions and set(mentions) != {u}:
        raise Refusal("question_unit_mismatch")
    return {"unit": u, "decimals": places, "factor": UNITS[u][0]}


def parse_f17(q, T):
    """Strict source-template parsers; preserve every word of each referent.

    Other wording requires reviewed, question-hash-bound bindings. These patterns
    implement SPEC §3a; they never infer a label or a referent from source answers.
    """
    t, text = q["question_type"], q["question"].strip()
    patterns = {
        "absolute_count": [
            (r"Precisely how many (.+?)\(s\) does this room contain\?", ("cat",)),
            (r"How many (.+?)\(s\) (?:are in|do we have in) this room\?", ("cat",))],
        "relative_count": [(r"Are (.+?)\(s\) more numerous than, less numerous than, or equal in number to (.+?)\(s\) in this room\?", ("a", "b"))],
        "absolute_distance_object": [
            (r"Quantify the shortest space separating the (.+?) from the (.+?) in meters\.", ("a", "b")),
            (r"What is the distance between the (.+?) and the (.+?) \(in meters\)\?", ("a", "b"))],
        "absolute_size_object": [(r"How many meters is the longest side of the (.+?)\?", ("a",))],
        "relative_size_object": [(r"Is the longest edge of the (.+?) or the (.+?) the (shorter|longer)\?", ("a", "b", "comparison"))],
        "relative_distance_object": [
            (r"From the closest point of each object, determine which among \((.+?)\) is nearest the (.+?)\. If multiple exist, use the nearest instance\.", ("cands", "target")),
            (r"Measuring from the closest point of each object, which of these objects \((.+?)\) is the closest to the (.+?)\?", ("cands", "target"))],
        "absolute_direction_object": [
            (r"Positioned at the (.+?) and oriented toward the (.+?), how many degrees counterclockwise should I turn to face the (.+?)\?", ("stand", "face", "query")),
            (r"From the (.+?), oriented toward the (.+?), what's the angle of rotation counterclockwise needed to look directly at the (.+?)\?", ("stand", "face", "query"))],
        "relative_direction_object": [
            (r"If I'm positioned at the (.+?) and oriented toward the (.+?), would the (.+?) be to the left or right of it\?", ("stand", "face", "query")),
            (r"If I am standing by the (.+?) and facing the (.+?), is the (.+?) to my left or right\?", ("stand", "face", "query"))],
    }
    for pattern, keys in patterns[t]:
        match = re.fullmatch(pattern, text, re.I)
        if match:
            result = dict(zip(keys, match.groups()))
            if "cands" in result: result["cands"] = [x.strip() for x in result["cands"].split(",")]
            return result
    return None


def validate_plan(q, plan, T):
    """Reviewed bindings cannot silently shorten a qualified referring phrase."""
    def normalized(s): return " ".join(s.lower().split())
    options = T.option_texts(q["options"])
    if len(options) != len(q["options"]) or len(set(normalized(v) for v in options.values())) != len(options):
        raise Refusal("ambiguous_or_malformed_options")
    if q["question_type"] not in F17: return
    text = normalized(q["question"])
    for key in ("cat", "a", "b", "target", "stand", "face", "query", "obj", "ref"):
        if key in plan:
            phrase = plan[key]
            if not isinstance(phrase, str) or not phrase.strip() or normalized(phrase) not in text:
                raise Refusal("binding_referent_not_in_question", key)
    # For unknown source wording a reviewed binding must explicitly attest full
    # referring-expression preservation; strict parsers establish it directly.
    if q["question_type"] in F17 and not parse_f17(q, T) and plan.get("full_referents_reviewed") is not True:
        defer("unreviewed_full_referents")
    if q["question_type"] == "relative_size_object" and plan.get("comparison") not in ("shorter", "longer"):
        raise Refusal("missing_size_comparison")
    if q["question_type"] in ("relative_size_object", "relative_distance_object"):
        referents = [plan["a"], plan["b"]] if "a" in plan else plan["cands"]
        if sorted(map(normalized, T.option_texts(q["options"]).values())) != sorted(map(normalized, referents)):
            raise Refusal("candidate_option_mismatch")
    if q["question_type"] == "relative_count":
        if sorted(map(normalized, T.option_texts(q["options"]).values())) != ["equal number", "fewer", "more"]:
            raise Refusal("count_option_mismatch")
