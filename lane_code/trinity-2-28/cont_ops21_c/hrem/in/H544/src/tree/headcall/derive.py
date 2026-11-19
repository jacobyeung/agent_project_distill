"""Derived text: what a trace states after its head calls, computed only from the calls and their printed responses.

A converted row keeps its target twice: `target` (the text with GT responses) and `target_template`, where every
response is the marker ⟦R<i>⟧ (call i) and every derived value is ⟦D<k>⟧ (item k of `head_derived`). An item
names the calls (or earlier items) it reads:

  point               {"pose": i, "depth": j}        "point (x, y, z)": unproject(call j's point, depth j, pose i)
  moved               {"from": i, "to": j}           "moved X m, turned Y" between two pose responses (from None:
                                                     the frame-1 origin, position 0 and heading 0 by definition)
  relative_direction  {"points": [a, b, c]}          "N degrees left of straight ahead, in front" (stand, face, target)
  absolute_direction  {"points": [a, b, c]}          "N degrees" counterclockwise from facing b to facing c
  distance            {"points": [a, b], "unit"}     "X m" (or "N cm"): the distance between two derived points
  closest             {"anchors": [a..], "candidates": [[name, p], ..], "unit"}
                                                     "chair 1.20 m; lamp 2.31 m, so the closest is the chair": each
                                                     candidate's distance to its nearest anchor point
  ego_motion          {"from": i, "to": j}           "X m forward, Y m right and Z m down relative to its orientation
                                                     at the first frame, turned W": the second camera's displacement
                                                     in the first camera's horizontal heading frame (from None: the
                                                     frame-1 origin)
  movement_direction  {"motion": k}                  "Forward motion dominates, so the primary direction is Forward":
                                                     the larger horizontal component of ego_motion item k
  displacement        {"motion": k, "unit"}          "about X m": the straight-line length of ego_motion item k

Every value is computed from the response text as printed (rounded), and a point is used downstream as printed, so
the student can reproduce each derived number from its own calls. render() fills a template from any responses
(GT, head, or a scheduled-sampling mix), and decision() reads the row's decision from the derived values; the same
decision() and same_decision() serve the converters (a row is kept with calls only when its GT responses reach the
GT answer), scheduled sampling (swaps that change the decision are rejected) and the gate (the head's responses must
reach the decision the GT responses reach).
"""
import math
import re

from . import protocol as P
from .geometry import unproject

MARK = re.compile("⟦([RD])(\\d+)⟧")
ABS_DIRECTION_TOL_DEG = 15.0
NUMERIC_REL_TOL = 0.10
NUMERIC_ABS_TOL_M = 0.10
QUADRANTS = ("front-left", "front-right", "back-left", "back-right")
MOVEMENTS = ("forward", "backward", "left", "right")
CM_PER_M = 100.0


def marker(kind, index):
    return "⟦%s%d⟧" % (kind, index)


def response_marker(index):
    return P.RESPONSE_OPEN + marker("R", index) + P.RESPONSE_CLOSE


def printed_point(value):
    return tuple(float(P.num(v)) for v in value)


def point_text(value):
    return "point (%s, %s, %s)" % tuple(P.num(v) for v in value)


def horizontal_angle(stand, face, target):
    """Signed angle (degrees, left positive) from the stand->face direction to the stand->target direction."""
    u = (face[0] - stand[0], face[1] - stand[1])
    v = (target[0] - stand[0], target[1] - stand[1])
    if math.hypot(*u) < 1e-9 or math.hypot(*v) < 1e-9:
        raise ValueError("degenerate direction: two derived points coincide")
    return math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))


def direction_text(angle):
    return "%s of straight ahead, %s" % (P.turn(angle), "in front" if abs(angle) < 90 else "behind")


def counterclockwise(angle):
    return int(round(angle % 360.0)) % 360


def values_of(kinds, responses):
    """Call values parsed from response texts (None for an unreadable or error response)."""
    return [P.parse_response(kind, text) if text is not None else None for kind, text in zip(kinds, responses)]


def evaluate(items, values, points=None):
    """(texts, results) of every derived item from the calls' printed values; raises ValueError when an input is
    missing (an error response) or degenerate. points: {item index: (x, y, z)} replaces those point results (a
    diagnostic that re-derives the decision from other points, e.g. exact calibrated back-projections)."""
    texts, results = [], []
    for k, item in enumerate(items):
        kind = item["kind"]
        if kind == "point" and points is not None and k in points:
            texts.append(point_text(points[k]))
            results.append(tuple(points[k]))
        elif kind == "point":
            pose, depth = values[item["pose"]], values[item["depth"]]
            if not isinstance(pose, P.PoseValue) or not isinstance(depth, float):
                raise ValueError("a point needs a pose and a depth response")
            point = printed_point(unproject(item["at"], depth, pose))
            texts.append(point_text(point))
            results.append(point)
        elif kind == "moved":
            a = values[item["from"]] if item["from"] is not None else P.PoseValue((0.0, 0.0, 0.0), 0.0, 0.0)
            b = values[item["to"]]
            if not isinstance(a, P.PoseValue) or not isinstance(b, P.PoseValue):
                raise ValueError("moved needs two pose responses")
            moved = math.sqrt(sum((p - q) ** 2 for p, q in zip(a.position, b.position)))
            texts.append("moved %s m, turned %s" % (P.num(moved), P.turn(b.heading_deg - a.heading_deg)))
            results.append(moved)
        elif kind in ("relative_direction", "absolute_direction"):
            stand, face, target = (results[k] for k in item["points"])
            angle = horizontal_angle(stand, face, target)
            texts.append(direction_text(angle) if kind == "relative_direction" else "%d degrees" % counterclockwise(angle))
            results.append(angle)
        elif kind == "distance":
            a, b = (results[k] for k in item["points"])
            value = point_distance(a, b)
            texts.append(length_text(value, item.get("unit", "m")))
            results.append(value)
        elif kind == "closest":
            anchors = [results[k] for k in item["anchors"]]
            if not anchors or not item["candidates"]:
                raise ValueError("closest needs anchor and candidate points")
            distances = []
            for name, k in item["candidates"]:
                distances.append((name, min(point_distance(results[k], a) for a in anchors)))
            best = min(distances, key=lambda pair: pair[1])
            if sum(1 for _, d in distances if length_text(d, item.get("unit", "m")) ==
                   length_text(best[1], item.get("unit", "m"))) > 1:
                raise ValueError("degenerate closest: two candidates print the same distance")
            texts.append("%s, so the closest is the %s" % ("; ".join(
                "%s %s" % (name, length_text(d, item.get("unit", "m"))) for name, d in distances), best[0]))
            results.append(best[0])
        elif kind == "ego_motion":
            a = values[item["from"]] if item["from"] is not None else P.PoseValue((0.0, 0.0, 0.0), 0.0, 0.0)
            b = values[item["to"]]
            if not isinstance(a, P.PoseValue) or not isinstance(b, P.PoseValue):
                raise ValueError("ego_motion needs two pose responses")
            motion = ego_motion(a, b)
            texts.append(motion_text(motion))
            results.append(motion)
        elif kind == "movement_direction":
            label = movement_label(results[item["motion"]])
            texts.append("%s motion dominates, so the primary direction is %s" % (
                {"forward": "Forward", "backward": "Backward", "left": "Leftward", "right": "Rightward"}[label],
                label.capitalize()))
            results.append(label)
        elif kind == "displacement":
            forward, right, up, _ = results[item["motion"]]
            value = math.sqrt(forward ** 2 + right ** 2 + up ** 2)
            texts.append("about " + length_text(value, item.get("unit", "m")))
            results.append(value)
        else:
            raise ValueError("unknown derived item %r" % kind)
    return texts, results


def point_distance(a, b):
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(a, b)))


def length_text(metres, unit="m"):
    """A length as the trace prints it: metres with two decimals, or whole centimetres."""
    if unit == "cm":
        return "%d cm" % int(round(metres * CM_PER_M))
    if unit != "m":
        raise ValueError("unknown length unit %r" % (unit,))
    return "%s m" % P.num(metres)


def ego_motion(a, b):
    """(forward, right, up, turn_left_deg) of camera b relative to camera a: the displacement in a's horizontal
    heading frame (forward along a's heading, right 90 degrees clockwise of it, up along gravity) and b's heading
    minus a's, wrapped to [-180, 180)."""
    h = math.radians(a.heading_deg)
    forward_axis, right_axis = (-math.sin(h), math.cos(h)), (math.cos(h), math.sin(h))
    d = [q - p for p, q in zip(a.position, b.position)]
    forward = d[0] * forward_axis[0] + d[1] * forward_axis[1]
    right = d[0] * right_axis[0] + d[1] * right_axis[1]
    turn = (b.heading_deg - a.heading_deg + 180.0) % 360.0 - 180.0
    return forward, right, d[2], turn


def signed_text(value, positive, negative):
    return "%s m %s" % (P.num(abs(value)), positive if value >= 0 else negative)


def motion_text(motion):
    forward, right, up, turn = motion
    return "the camera moved %s and %s relative to its orientation at the first frame, and %s; it turned %s" % (
        signed_text(forward, "forward", "backward"), signed_text(right, "right", "left"),
        signed_text(up, "up", "down"), P.turn(turn))


def movement_label(motion):
    """The dominant horizontal direction of an ego_motion result (ties, as printed, are degenerate)."""
    forward, right = motion[0], motion[1]
    if P.num(abs(forward)) == P.num(abs(right)):
        raise ValueError("degenerate movement: forward and lateral components print equal")
    if abs(forward) > abs(right):
        return "forward" if forward > 0 else "backward"
    return "right" if right > 0 else "left"


def render(template, responses, texts):
    """Fill a template's ⟦R⟧ and ⟦D⟧ markers."""
    def fill(match):
        index = int(match.group(2))
        return responses[index] if match.group(1) == "R" else texts[index]
    out = MARK.sub(fill, template)
    if "⟦" in out or "⟧" in out:
        raise ValueError("unfilled marker")
    return out


def direction_label(angle, options):
    """The option a signed angle selects, for the option vocabularies of the direction questions (None if unknown)."""
    names = [o.strip().lower() for o in options]
    if set(names) <= set(QUADRANTS):
        label = ("front" if abs(angle) < 90 else "back") + "-" + ("left" if angle > 0 else "right")
    elif set(names) <= {"left", "right", "back"}:
        label = "back" if abs(angle) >= 135 else ("left" if angle > 0 else "right")
    elif set(names) <= {"left", "right"}:
        label = "left" if angle > 0 else "right"
    elif set(names) <= {"front", "back"}:
        label = "front" if abs(angle) < 90 else "back"
    else:
        return None
    return label if label in names else None


def option_text(row, letter):
    options = row.get("options") or (row.get("student_input") or {}).get("options") or []
    for option in options:
        head, _, body = option.partition(". ")
        if head.strip() == letter:
            return body
    return None


def option_bodies(row):
    options = row.get("options") or (row.get("student_input") or {}).get("options") or []
    return [o.partition(". ")[2] if ". " in o[:4] else o for o in options]


DECISION_KINDS = ("relative_direction", "absolute_direction", "distance", "closest", "movement_direction",
                  "displacement")


def decision(row, items, results):
    """The decision the derived values support (the row's final derived item that decides), or None:
      ('label', option text)  relative_direction, movement_direction
      ('angle', degrees)      absolute_direction (counterclockwise, 0..359)
      ('distance', metres)    distance, displacement
      ('closest', name)       closest
    Counts, orders and sizes state no derived quantity and have no decision."""
    found = None
    for item, result in zip(items, results):
        kind = item["kind"]
        if kind == "relative_direction":
            found = ("label", direction_label(result, option_bodies(row)))
        elif kind == "absolute_direction":
            found = ("angle", counterclockwise(result))
        elif kind in ("distance", "displacement"):
            found = ("distance", float(result))
        elif kind == "closest":
            found = ("closest", result.strip().lower())
        elif kind == "movement_direction":
            names = [o.strip().lower() for o in option_bodies(row)]
            found = ("label", result if result in names else None)
    return found


def same_decision(gt, pred):
    """Whether two decisions agree: labels and closest names exactly, angles within ABS_DIRECTION_TOL_DEG, distances
    within NUMERIC_REL_TOL of the reference (gt) or NUMERIC_ABS_TOL_M, whichever is larger. None when gt is None."""
    if gt is None:
        return None
    if pred is None or gt[0] != pred[0]:
        return False
    if gt[0] == "angle":
        return abs((pred[1] - gt[1] + 180.0) % 360.0 - 180.0) <= ABS_DIRECTION_TOL_DEG
    if gt[0] == "distance":
        return abs(pred[1] - gt[1]) <= max(NUMERIC_REL_TOL * gt[1], NUMERIC_ABS_TOL_M)
    return pred[1] is not None and pred[1] == gt[1]


def answer_decision(row, items):
    """The row's GT answer as a decision of the same kind its derived items reach (None without a deciding item)."""
    kinds = [item["kind"] for item in items if item["kind"] in DECISION_KINDS]
    if not kinds:
        return None
    kind, item = kinds[-1], [i for i in items if i["kind"] in DECISION_KINDS][-1]
    answer = str(row["answer"]).strip()
    if kind in ("relative_direction", "movement_direction"):
        return "label", (option_text(row, answer) or "").strip().lower() or None
    if kind == "closest":
        return "closest", (option_text(row, answer) or "").strip().lower() or None
    if kind == "absolute_direction":
        return "angle", float(answer) % 360.0
    scale = CM_PER_M if item.get("unit", "m") == "cm" else 1.0
    return "distance", float(answer) / scale


def answer_supported(row, items, results):
    """True when the derived decision agrees with the row's GT answer (same_decision with the answer as the
    reference), or the row has no derived decision."""
    gt = answer_decision(row, items)
    if gt is None:
        return True
    if gt[1] is None:
        return False
    return bool(same_decision(gt, decision(row, items, results)))


def point_items(items):
    return [k for k, item in enumerate(items) if item["kind"] == "point"]
