from copy import deepcopy
import hashlib
import json
import math

SCHEMA = "s1-predicted-geometry-v2"
POLICY = "bound-per-capture-geometry-refusals-v1"
ARMS = ("unflagged", "scripted")
NONFATAL_CODE = "reference_camera_up_opposes_gravity"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def attempt(operation, geometry_error):
    try:
        return dict(status="PASS", data=operation(), error=None)
    except geometry_error as error:
        message = str(error)
        code = getattr(error, "code", None) or message.split(":", 1)[0] or type(error).__name__
        if code != NONFATAL_CODE:
            raise
        if not isinstance(code, str) or not message:
            raise ValueError("A geometry contract refusal lacks its code or message") from error
        return dict(status="REFUSED", data=None,
                    error=dict(code=code, message=message, exception=type(error).__name__))


def gravity_diagnostics(rotations, head_gravity, tower_gravity, source_hw):
    import numpy as np
    rotations = np.asarray(rotations, dtype=np.float64)
    head = np.asarray(head_gravity, dtype=np.float64)
    tower = np.asarray(tower_gravity, dtype=np.float64)
    if (rotations.shape != (32, 3, 3) or head.shape != (3,) or tower.shape != (3,)
            or not all(np.isfinite(value).all() for value in (rotations, head, tower))
            or min(np.linalg.norm(head), np.linalg.norm(tower)) < 1e-6):
        raise ValueError("The per-capture gravity telemetry is incomplete")
    head, tower = head/np.linalg.norm(head), tower/np.linalg.norm(tower)
    up = rotations[:, 2, :]
    pitch = np.degrees(np.arcsin(np.clip(up[:, 2], -1., 1.)))
    roll = np.degrees(np.arctan2(up[:, 0], -up[:, 1]))
    selected = roll[pitch > -60.]
    return dict(stored_hw=[int(value) for value in source_hw], head_gravity=head.tolist(),
                tower_gravity=tower.tolist(), pitch_deg=float(pitch[0]), roll_deg=float(roll[0]),
                guard_margin=float(-rotations[0, 2, 1]), in_plane_norm=float(np.linalg.norm(up[0, :2])),
                median_roll_pitch_above_minus60_deg=float(np.median(selected)) if len(selected) else None,
                frames_pitch_above_minus60=int(len(selected)), tower_reference_margin=float(-tower[1]))


def validate(manifest, checkpoint, expected=None):
    if (manifest.get("schema") != SCHEMA or manifest.get("policy") != POLICY
            or manifest.get("checkpoint") != checkpoint or not manifest.get("records")
            or not isinstance(manifest.get("videos"), dict)):
        raise ValueError("The geometry disposition manifest is unbound or empty")
    names, clips, videos = set(), set(), {}
    for record in manifest["records"]:
        native, clip = record.get("native"), record.get("clip")
        if (not isinstance(native, str) or not native or native in names
                or not isinstance(clip, str) or len(clip) != 64 or clip in clips
                or record.get("checkpoint") != checkpoint):
            raise ValueError("Geometry capture, clip or checkpoint identity differs")
        names.add(native)
        clips.add(clip)
        if record.get("status") == "PASS":
            if record.get("error") is not None or not isinstance(record.get("output"), dict):
                raise ValueError("Passed geometry has no bound output or contains an error")
            videos[clip] = record["output"]
        elif record.get("status") == "REFUSED":
            error = record.get("error")
            if (not isinstance(error, dict)
                    or error.get("code") != NONFATAL_CODE
                    or any(not isinstance(error.get(key), str) or not error[key]
                           for key in ("code", "message", "exception"))):
                raise ValueError("A refused capture lacks its contract error")
        else:
            raise ValueError("A geometry capture has no terminal disposition")
    if videos != manifest["videos"]:
        raise ValueError("Passed geometry and the admitted video map differ")
    if expected is not None and (len(expected) != len(set(expected)) or names != set(expected)):
        raise ValueError("Geometry capture membership differs from the bound cohort")
    return manifest


def item_refusals(tasks, manifest):
    validate(manifest, manifest["checkpoint"])
    by_native = {record["native"]:record for record in manifest["records"]}
    result, seen = {}, set()
    for task in tasks:
        if task["id"] in seen or task["native"] not in by_native:
            raise ValueError("An item has duplicate or unbound geometry membership")
        seen.add(task["id"])
        record = by_native[task["native"]]
        if record["status"] == "REFUSED":
            result[task["id"]] = dict(
                capture=task["native"], clip=record["clip"], checkpoint=deepcopy(manifest["checkpoint"]),
                capture_record_sha256=digest(record), **record["error"])
    return result


def refusal_pair(task, request, question_unit):
    refusal = request["geometry_refusals"][task["id"]]
    perception = request["perceptions"][task["id"]]
    if (refusal["capture"] != task["native"] or refusal["checkpoint"] != request["artifact"]
            or perception.get("geometry_refusal") != refusal):
        raise ValueError("The item refusal differs from its bound capture or checkpoint")
    prefill = digest(dict(not_executed=True, geometry_refusal=refusal,
                         manifest=request["grounding"]["geometry_manifest"]))
    released = task.get("released_answer_in_options", task.get("released_answer"))
    row = dict(
        key="devrows:"+task["id"], room=task["room"], question_type=task["question_type"],
        stratum=task["stratum"], scores=dict(answer=0., released_answer=None if released is None else 0.),
        capped=False, no_answer=True, called=False, call_errors=0, version_errors=0,
        budget_truncated_calls=0, budget_truncated_call_kinds=[], decode_executed=False,
        sampled_tokens=0, injected_tokens=0, total_tokens=0,
        checkpoint_sha256=request["artifact"]["sha256"], perception=perception,
        mask_source=perception["mask_source"], perception_identity=digest(perception),
        prefill_identity=prefill, binding=request["binding"], question_unit=question_unit,
        geometry_refusal=refusal, seconds=0.)
    return [dict(deepcopy(row), arm=arm) for arm in ARMS]


def paired_item(task, request, question_unit, serve):
    if task["id"] in request["geometry_refusals"]:
        return refusal_pair(task, request, question_unit)
    return serve()


def compare_refusals(pilot, full):
    def membership(records):
        names = [record["native"] for record in records]
        if (len(names) != 84 or len(set(names)) != 84
                or any(record["status"] not in ("PASS", "REFUSED") for record in records)):
            raise ValueError("Refusal comparison requires all 84 capture dispositions")
        return set(names), {record["native"] for record in records if record["status"] == "REFUSED"}
    pilot_names, pilot_refused = membership(pilot)
    full_names, full_refused = membership(full)
    if pilot_names != full_names:
        raise ValueError("Pilot and full-read geometry cohorts differ")
    return dict(pilot_refused=sorted(pilot_refused), full_refused=sorted(full_refused),
                pilot_passed_full_refused=sorted(full_refused-pilot_refused),
                pilot_refused_full_passed=sorted(pilot_refused-full_refused),
                unchanged=pilot_refused == full_refused, difference_refuses_read=False)


def score_report(rows, expected):
    membership = {row["key"]:row for row in expected}
    if len(membership) != len(expected):
        raise ValueError("The score denominator repeats an item")
    observed = {arm:{} for arm in ARMS}
    for row in rows:
        arm, key = row.get("arm"), row.get("key")
        if arm not in observed or key not in membership or key in observed[arm]:
            raise ValueError("The score records contain a duplicate or foreign arm/item")
        bound = membership[key]
        refused = bool(row.get("geometry_refusal"))
        score = row.get("scores", {}).get(bound["label"])
        if (refused != bound["geometry_refused"] or type(score) not in (int, float)
                or not math.isfinite(score) or not 0 <= score <= 1
                or refused and (score != 0 or row.get("called") is not False
                                or row.get("decode_executed") is not False or "decode" in row)):
            raise ValueError("A bound geometry refusal or score differs")
        observed[arm][key] = row
    groups = dict(distance={"object_abs_distance"}, room={"room_size_estimation"},
                  camera={"camera_displacement", "camera_movement_direction", "camera_rotation"})
    result = {}
    for group, families in groups.items():
        keys = [row["key"] for row in expected if row["family"] in families]
        result[group] = dict(geometry_refused_items=sum(membership[key]["geometry_refused"] for key in keys))
        for scope in ("with_refusals", "without_refusals"):
            subset = [key for key in keys if scope == "with_refusals" or not membership[key]["geometry_refused"]]
            result[group][scope] = {}
            for arm in ARMS:
                missing = [key for key in subset if key not in observed[arm]]
                score = None if missing or not subset else 100*sum(
                    observed[arm][key]["scores"][membership[key]["label"]] for key in subset)/len(subset)
                result[group][scope][arm] = dict(expected_items=len(subset),
                    observed_items=len(subset)-len(missing), missing_keys=missing, score_pct=score)
    return result
