import collections
import math

from . import rehearsal


POLICY = "all_rank_native_v1"


def report(records, binding, recipe, step, device):
    world = recipe["world_size"]
    expected = collections.Counter(recipe["mix"])
    reasons, ranks = [], []
    if len(records) != world or sorted(item.get("rank", -1) for item in records) != list(range(world)):
        reasons.append("rank_membership")
    for item in records:
        shapes = item.get("shapes", [])
        streams = collections.Counter(shape.get("stream") for shape in shapes)
        errors = []
        if set(streams) != set(expected) or set(item.get("stream_means", {})) != set(expected):
            errors.append("stream_coverage")
        if streams != expected:
            errors.append("microstep_counts")
        if (item.get("skipped_microsteps")
                or any(shape.get("substituted_from") or shape.get("encode_errors") or shape.get("own_skip")
                       for shape in shapes)):
            errors.append("skipped_or_substituted_rows")
        for key in ("components", "stream_means", "gradient_norms"):
            values = item.get(key)
            if not isinstance(values, dict) or not values or any(
                    type(value) not in (float, int) or not math.isfinite(value) for value in values.values()):
                errors.append("nonfinite_or_missing_"+key)
        if item.get("step") != step:
            errors.append("optimizer_step")
        ranks.append(dict(rank=item.get("rank"), status="FAIL" if errors else "PASS", errors=errors,
                          streams=dict(streams), components=item.get("components"),
                          gradient_norms=item.get("gradient_norms"), wall_seconds=item.get("wall_seconds"),
                          peak_allocated_bytes=item.get("peak_allocated_bytes"),
                          peak_reserved_bytes=item.get("peak_reserved_bytes")))
        reasons.extend(f"rank{item.get('rank')}:{error}" for error in errors)
    if device != ("cpu" if rehearsal.enabled() else "cuda"):
        reasons.append("device")
    return dict(schema="s1-native-first-step-v1", status="FAIL" if reasons else "PASS",
                binding=binding, step=step, world_size=world, device=device, ranks=ranks,
                expected_per_rank=dict(expected),
                errors=reasons, rehearsal=rehearsal.enabled(),
                real_gpu_step=device == "cuda" and not rehearsal.enabled(), production_authorized=False)
