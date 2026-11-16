"""The headcall training block: phase 2's row handling inside the full fine-tuning trainer (ddp_training.train).

Admission keeps only a fixed set of row fields (provisional._load_candidate_rows), so a row's head calls cannot ride in
the candidate index. They come from a pinned sidecar instead, joined at train time the way the label bank is:

  sidecar   gzip JSONL, sorted by qid. Line 1 is the header {"schema": SIDECAR_SCHEMA, "arm", "entries", "source"}; every
            other line is one row's entry:
              {"qid", "kind": "headcall", "target_sha256", "input_sha256", "head_calls", "target_template",
               "head_derived"}  (arm HC: a head-call trace row)
              {"qid", "kind": "queries", "target_sha256", "input_sha256", "queries"}  (arms HX and HA: the twin of an
               HC head-call row; queries are that row's depth calls, [{frame, point, depth_m}])
            target_sha256 is the SHA-256 of the admitted row's target text and input_sha256 its input identity
            (auxiliary_targets.input_identity), so an entry binds to exactly one admitted row. A headcall entry's
            template must re-render the admitted target from its GT responses.

  every entry  the row's queried depth points go first into its point-depth targets (the bank's points fill the
            remaining slots), and the 16 carriers are inserted even when the bank has no label for the scene. HC, HX
            and HA therefore see the same carriers and depth targets on the same rows; only the target text differs.
  headcall  tool responses are masked from the LM loss (<tool_response> through </tool_response>), and scheduled
            sampling (HC only) swaps GT responses for the student's own head answers before backward.

Scheduled sampling under FSDP: a head session is one no-grad forward of the row's carrier-bearing prompt, and every FSDP
forward is a collective. Each rank therefore runs as many session forwards per micro-batch as the busiest rank (one
all-reduce of the count); a rank with fewer sampled rows runs no-grad forwards on its own first prompt, whose results
it discards. Only rows with at least one chosen call get a session.
"""
import gzip
import hashlib
import io
import json
import math
from collections import Counter

SCHEMA = "headcall-fullft-v1"
SIDECAR_SCHEMA = "headcall-sidecar-v1"
ARMS = ("HC", "HX", "HA")
KINDS = {"HC": "headcall", "HX": "queries", "HA": "queries"}
DEPTH_QUERIES = "queried_first_then_bank_v1"
CARRIERS = "forced_on_sidecar_rows_v1"
SAMPLING_DEFAULTS = {"start_p": 0.0, "end_p": 0.5, "start_step": 0, "end_step": 1000, "seed": 17,
                     "depth_rel_tol": 0.10, "depth_abs_tol_m": 0.20, "pose_pos_tol_m": 0.25,
                     "pose_heading_tol_deg": 10.0, "pose_pitch_tol_deg": 10.0, "pose_roll_tol_deg": 10.0,
                     "pose_view_tol_deg": 10.0}
KEYS = {"schema", "arm", "sidecar", "scheduled_sampling", "depth_queries", "carriers"}
HEX64 = set("0123456789abcdef")
FORCE = "force_carriers"
GROUPS = 16


# ---------------------------------------------------------------------------------------------- config

def normalize(value):
    """The canonical headcall block, or refuse it. HC samples (scheduled_sampling an object); HX and HA never do."""
    if not isinstance(value, dict) or set(value) - KEYS or value.get("schema", SCHEMA) != SCHEMA:
        raise ValueError(f"headcall keys must be a subset of {sorted(KEYS)} with schema {SCHEMA}")
    arm = value.get("arm")
    if arm not in ARMS:
        raise ValueError(f"headcall arm must be one of {ARMS}")
    pin = value.get("sidecar")
    if (not isinstance(pin, dict) or set(pin) != {"path", "sha256"} or not isinstance(pin["path"], str) or not pin["path"]
            or not isinstance(pin["sha256"], str) or len(pin["sha256"]) != 64 or set(pin["sha256"]) - HEX64):
        raise ValueError("headcall sidecar must be {path, sha256} with a lowercase sha256")
    if value.get("depth_queries", DEPTH_QUERIES) != DEPTH_QUERIES or value.get("carriers", CARRIERS) != CARRIERS:
        raise ValueError(f"headcall depth_queries and carriers are fixed at {DEPTH_QUERIES} and {CARRIERS}")
    sampling = value.get("scheduled_sampling")
    if arm == "HC":
        if not isinstance(sampling, dict) or set(sampling) - set(SAMPLING_DEFAULTS):
            raise ValueError(f"HC needs scheduled_sampling with keys from {sorted(SAMPLING_DEFAULTS)}")
        sampling = {**SAMPLING_DEFAULTS, **sampling}
        for key in ("start_step", "end_step", "seed"):
            if type(sampling[key]) is not int or sampling[key] < 0:
                raise ValueError(f"scheduled_sampling {key} must be a non-negative integer")
        for key in set(SAMPLING_DEFAULTS) - {"start_step", "end_step", "seed"}:
            number = sampling[key]
            if type(number) not in (int, float) or not math.isfinite(number) or number < 0:
                raise ValueError(f"scheduled_sampling {key} must be a finite non-negative number")
            sampling[key] = float(number)
        if not (0 <= sampling["start_p"] <= 1 and 0 <= sampling["end_p"] <= 1) or sampling["end_step"] <= sampling["start_step"]:
            raise ValueError("scheduled_sampling needs probabilities in [0, 1] and end_step > start_step")
    elif sampling is not None:
        raise ValueError("Only the head-call arm HC samples its own head answers")
    result = {"schema": SCHEMA, "arm": arm, "sidecar": {"path": pin["path"], "sha256": pin["sha256"]},
              "scheduled_sampling": sampling, "depth_queries": DEPTH_QUERIES, "carriers": CARRIERS}
    return json.loads(json.dumps(result, sort_keys=True))


def check_camera(camera):
    """The headcall block needs the camera head with the point-depth head and the PD row routing (every labelled
    question row trains the heads): queried points supervise the depth head, and Cambrian-P routing would strip the
    question rows' carriers."""
    from student_pilot.camera_config import CAMBRIAN_P_ROUTING
    from student_pilot.point_depth_head import point_depth_enabled
    if camera is None or not point_depth_enabled(camera.get("point_depth")):
        raise ValueError("The headcall block needs the camera head with its point-depth head")
    if camera.get("row_routing") == CAMBRIAN_P_ROUTING:
        raise ValueError("The headcall block trains question rows with carriers; Cambrian-P routing strips them")


# ---------------------------------------------------------------------------------------------- sidecar

def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def depth_queries(entry):
    """[(frame, (x, y), depth_m)] of an entry's depth calls, in call order: one rule for HC's head calls and for the
    twins' query lists, so the arms supervise the same points."""
    if entry["kind"] == "headcall":
        return [(int(r["frame"]), (float(r["point"][0]), float(r["point"][1])), float(r["gt"]["depth_m"]))
                for r in entry["head_calls"] if r["name"] == "depth"]
    return [(int(q["frame"]), (float(q["point"][0]), float(q["point"][1])), float(q["depth_m"])) for q in entry["queries"]]


def twin_queries(head_calls):
    """The twins' query list of one HC head-call row (sidecar builder)."""
    return [{"frame": int(r["frame"]), "point": [float(r["point"][0]), float(r["point"][1])],
             "depth_m": float(r["gt"]["depth_m"])} for r in head_calls if r["name"] == "depth"]


def write_sidecar(path, arm, entries, source):
    """Deterministic gzip JSONL (mtime 0, sorted by qid); returns its {path, sha256}."""
    entries = sorted(entries, key=lambda item: item["qid"])
    if len({item["qid"] for item in entries}) != len(entries):
        raise ValueError("A sidecar names a qid twice")
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0, compresslevel=6) as stream:
        header = {"schema": SIDECAR_SCHEMA, "arm": arm, "entries": len(entries), "source": source}
        stream.write((json.dumps(header, sort_keys=True) + "\n").encode())
        for item in entries:
            stream.write((json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n").encode())
    data = buffer.getvalue()
    with open(path, "xb") as handle:
        handle.write(data)
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


def read_sidecar(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        header = json.loads(stream.readline())
        entries = [json.loads(line) for line in stream if line.strip()]
    if header.get("schema") != SIDECAR_SCHEMA or header.get("entries") != len(entries):
        raise ValueError("Not a complete headcall sidecar")
    return header, entries


def check_entry(entry, row, arm):
    from student_pilot.auxiliary_targets import input_identity
    from .protocol import exchanges
    from .training import swap_targets

    if entry.get("kind") != KINDS[arm]:
        raise ValueError(f"Arm {arm} sidecar entries are {KINDS[arm]}, not {entry.get('kind')} ({row['qid']})")
    if entry["target_sha256"] != text_sha256(row["target"]):
        raise ValueError(f"Sidecar entry target differs from the admitted row target ({row['qid']})")
    if entry["input_sha256"] != input_identity(row):
        raise ValueError(f"Sidecar entry input differs from the admitted row input ({row['qid']})")
    queries = depth_queries(entry)
    for frame, point, depth in queries:
        if frame not in range(2, 33, 2) or not all(0 <= v <= 1000 for v in point) or not (math.isfinite(depth) and depth > 0):
            raise ValueError(f"Sidecar depth query outside the heads' frames, grid or range ({row['qid']})")
    if entry["kind"] == "headcall":
        calls = entry["head_calls"]
        if not calls or len(exchanges(row["target"])) != len(calls):
            raise ValueError(f"A head-call row's target exchanges differ from its head calls ({row['qid']})")
        rendered = swap_targets({"head_calls": calls, "head_derived": entry["head_derived"],
                                 "target_template": entry["target_template"]}, [r["response"] for r in calls])
        if rendered != row["target"]:
            raise ValueError(f"A head-call row's template does not re-render its admitted target ({row['qid']})")
    return queries


def join(rows, block, resolve=None):
    """Per-row sidecar entries (None for rows without one) in row order, and the join audit. Every sidecar qid must be
    an admitted row; nothing is dropped or invented."""
    from student_pilot.auxiliary_targets import verify

    path = verify(block["sidecar"]) if resolve is None else verify({**block["sidecar"], "path": str(resolve(block["sidecar"]["path"]))})
    header, entries = read_sidecar(path)
    if header.get("arm") != block["arm"]:
        raise ValueError("The sidecar belongs to another arm")
    by_qid = {row["qid"]: index for index, row in enumerate(rows)}
    joined = [None] * len(rows)
    audit = Counter()
    categories = Counter()
    for entry in entries:
        if entry["qid"] not in by_qid:
            raise ValueError(f"Sidecar qid {entry['qid']} is not an admitted training row")
        index = by_qid[entry["qid"]]
        if joined[index] is not None:
            raise ValueError("A sidecar names a qid twice")
        row = rows[index]
        queries = check_entry(entry, row, block["arm"])
        joined[index] = entry
        audit[entry["kind"] + "_rows"] += 1
        audit["depth_queries"] += len(queries)
        if entry["kind"] == "headcall":
            audit["head_calls"] += len(entry["head_calls"])
        categories[row["category"]] += 1
    report = {"schema": "headcall-join-v1", "arm": block["arm"], "sidecar": block["sidecar"], "admitted_rows": len(rows),
              "sidecar_rows": len(entries), **dict(sorted(audit.items())),
              "rows_by_category": dict(sorted(categories.items()))}
    return joined, report


def attach(rows, joined):
    return [row if entry is None else {**row, "_headcall": entry} for row, entry in zip(rows, joined)]


# ---------------------------------------------------------------------------------------------- encoding

def merge_point_depth(record, entry, stats=None):
    """The row's queried depth points first in each group's slots, then the bank's points that still fit (the bank's K
    points per frame is the batch layout). Raises when a group has more queries than slots."""
    pd = record.get("point_depth")
    if pd is None:
        raise ValueError("Head-call rows need point-depth targets in their camera record")
    slots = len(pd["mask"][0])
    queried = [[] for _ in range(GROUPS)]
    for frame, point, depth in depth_queries(entry):
        queried[frame // 2 - 1].append((list(point), depth))
    uv, depth, mask = [], [], []
    for g in range(GROUPS):
        if len(queried[g]) > slots:
            raise ValueError("more depth queries in group %d than points per frame" % g)
        bank = [(list(map(float, pd["uv"][g][k])), float(pd["depth"][g][k])) for k in range(slots) if pd["mask"][g][k]]
        chosen = (queried[g] + bank)[:slots]
        pad = slots - len(chosen)
        uv.append([p for p, _ in chosen] + [[0.0, 0.0]] * pad)
        depth.append([d for _, d in chosen] + [0.0] * pad)
        mask.append([True] * len(chosen) + [False] * pad)
        if stats is not None:
            stats["queried_depth_points"] += len(queried[g])
            stats["bank_depth_points_displaced"] += max(0, len(queried[g]) + len(bank) - slots)
    return dict(record, point_depth={"uv": uv, "depth": depth, "mask": mask})


def prepare_row(row, stats=None):
    """The row the encoder sees: for a sidecar row, its camera record with the queried points merged and carriers
    forced. Other rows are returned unchanged."""
    entry = row.get("_headcall")
    if entry is None:
        return row
    if "_camera" not in row:
        raise ValueError("head-call rows train with the camera head: row %s has no camera record" % row.get("qid"))
    record = merge_point_depth(dict(row["_camera"]), entry, stats)
    record[FORCE] = True
    return {**row, "_camera": record}


def is_headcall(row):
    entry = row.get("_headcall")
    return entry is not None and entry["kind"] == "headcall"


def finish_encoding(batch, row, tokenizer, stats=None):
    """The carrier check on every sidecar row, and tool-response masking on a head-call row."""
    from . import phase1
    from .training import IGNORE, mask_tool_responses, tool_token_ids

    if row.get("_headcall") is None:
        return batch
    positions = batch.get("aux_camera_positions")
    if positions is None or bool((positions < 0).any()):
        raise ValueError("a sidecar row must carry the 16 carriers")
    phase1.check_carriers(batch["input_ids"][0].tolist(), tokenizer)
    if stats is not None:
        stats["sidecar_rows_encoded"] += 1
    if not is_headcall(row):
        return batch
    supervised_before = int((batch["labels"] != IGNORE).sum())
    labels = mask_tool_responses(batch["input_ids"][0], batch["labels"][0], tool_token_ids(tokenizer))
    batch = dict(batch)
    batch["labels"] = labels[None] if labels.ndim == 1 else labels
    if stats is not None:
        stats["headcall_rows_encoded"] += 1
        stats["masked_response_tokens"] += supervised_before - int((batch["labels"] != IGNORE).sum())
    return batch


# ---------------------------------------------------------------------------------------------- scheduled sampling

class Sampling(object):
    """Scheduled-sampling state of one rank: the sampler, the per-micro-batch encodings, the step counters."""

    def __init__(self, settings, heads_factory=None):
        from .training import Schedule, ScheduledSampler
        tolerances = {key: settings[key] for key in SAMPLING_DEFAULTS if key.endswith(("_tol", "_tol_m", "_tol_deg"))}
        self.settings = settings
        self.sampler = ScheduledSampler(Schedule(settings["start_p"], settings["end_p"], settings["start_step"],
                                                 settings["end_step"]), None, seed=settings["seed"], **tolerances)
        self.heads_factory = heads_factory or default_heads_factory
        self.pending = {}
        self.stats = Counter()

    def register(self, collated, rows, encodings, processor):
        self.pending[id(collated)] = (collated["input_ids"], rows, encodings, processor)

    def take(self, collated):
        entry = self.pending.pop(id(collated), None)
        if entry is None or entry[0] is not collated["input_ids"]:
            raise ValueError("A training micro-batch reached backward without its registered head-call encodings")
        return entry[1:]

    def step_stats(self):
        """This step's counters plus the sampler's running totals (cumulative_*) on this rank."""
        stats, self.stats = dict(self.stats), Counter()
        stats.update(cumulative_attempted_swaps=self.sampler.attempted_swaps,
                     cumulative_accepted_swaps=self.sampler.accepted_swaps,
                     cumulative_rejected_swaps=self.sampler.rejected_swaps,
                     cumulative_rejected_rows=self.sampler.rejected_rows)
        return stats


def default_heads_factory(model, prompt, forward_context):
    """Phase1Heads over a session from one no-grad forward of the row's carrier-bearing prompt (with its geometry
    features when the model has a geometry input: phase1.session_forward)."""
    from . import phase1
    from .heads import Phase1Heads
    session = phase1.session_forward(model, prompt, forward_context=forward_context)
    return Phase1Heads.from_session(session)


def prompt_end(encoding):
    from .training import IGNORE
    labels = encoding["labels"][0]
    supervised = (labels != IGNORE).nonzero()
    if not len(supervised):
        raise ValueError("an encoding without supervised tokens")
    return int(supervised[0])


def prompt_batch(encoding, device=None):
    """The carrier-bearing prompt of a single-row training encoding (everything before the first target token)."""
    end = prompt_end(encoding)
    out = {}
    for key in ("input_ids", "attention_mask", "mm_token_type_ids"):
        if key in encoding:
            out[key] = encoding[key][:, :end]
    for key in ("pixel_values_videos", "video_grid_thw", "aux_camera_positions", "geometry_features",
                "aux_g3t_cam_tokens", "aux_g3t_pose_9d", "aux_g3t_gravity_up", "aux_g3t_step_scale"):
        if key in encoding:
            out[key] = encoding[key]
    if device is not None:
        out = {k: v.to(device) for k, v in out.items()}
    return out


def splice(processor, encoding, row, target, max_length=None):
    """The encoding with a new target: the prompt (pixels, carriers, camera targets) unchanged, the target tokens
    re-encoded by the trainer's training_text, tool responses masked, right padding to a multiple of 8 as the trainer
    pads. Returns None when the new target would exceed max_length (the swap is then rejected)."""
    import torch
    import torch.nn.functional as F
    from student_pilot.batches import training_text
    from student_pilot.ddp_core import SEQUENCE_AUXILIARY
    from .training import IGNORE, mask_tool_responses, tool_token_ids

    if set(encoding) & set(SEQUENCE_AUXILIARY):
        raise ValueError("token-aligned auxiliary targets cannot follow a re-rendered head-call target")
    inputs = row["student_input"]
    _, suffix = training_text(processor, inputs["question"], inputs["options"] or [], target)
    suffix_ids = processor.tokenizer.encode(suffix, add_special_tokens=False)
    end = prompt_end(encoding)
    length = end + len(suffix_ids)
    padded = int(math.ceil(length / 8.0)) * 8
    if max_length is not None and padded > max_length:
        return None
    pad = processor.tokenizer.pad_token_id
    ids = torch.cat([encoding["input_ids"][:, :end], torch.tensor([suffix_ids], dtype=encoding["input_ids"].dtype)], 1)
    out = dict(encoding)
    out["input_ids"] = F.pad(ids, (0, padded - length), value=pad)
    out["attention_mask"] = F.pad(torch.ones_like(ids), (0, padded - length), value=0)
    if "mm_token_type_ids" in encoding:
        out["mm_token_type_ids"] = F.pad(encoding["mm_token_type_ids"][:, :end], (0, padded - end), value=0)
    labels = torch.full_like(out["input_ids"], IGNORE)
    labels[0, end:length] = torch.tensor(suffix_ids, dtype=labels.dtype)
    out["labels"] = mask_tool_responses(out["input_ids"][0], labels[0], tool_token_ids(processor.tokenizer))[None]
    return out


def matched_count(count, fsdp, process_group, device):
    """The busiest rank's session-forward count (FSDP: every rank runs that many forwards)."""
    if not fsdp:
        return count
    import torch
    import torch.distributed as dist
    value = torch.tensor([count], dtype=torch.int64, device=device)
    dist.all_reduce(value, op=dist.ReduceOp.MAX, group=process_group)
    return int(value.item())


def discarded_forward(model, prompt, forward_context=None):
    """A no-grad forward whose result is dropped: it keeps this rank's FSDP collectives matched with the busiest rank.
    It runs exactly as a session forward does, geometry features included (phase1.GeometryContext)."""
    import torch
    from .phase1 import GeometryContext, split_geometry
    prompt, features = split_geometry(prompt)
    feed = {k: v for k, v in prompt.items() if not k.startswith("aux_")}
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad(), GeometryContext(model, features, forward_context):
            model(**feed, use_cache=False, logits_to_keep=1)
    finally:
        model.train(was_training)


def scheduled_batch(sampling, model, batch, rows, encodings, processor, weights, step, forward_context=None,
                    process_group=None, fsdp=False, max_length=None):
    """The micro-batch after scheduled sampling of its head-call rows (the same tensors when nothing changed)."""
    from student_pilot.ddp_core import collate_rows
    from .heads import HeadContext

    sampler, stats = sampling.sampler, sampling.stats
    device = batch["input_ids"].device
    # The sampler reads the head calls, template and derived items at the row's top level (training.ScheduledSampler).
    samples = [{**row, **{key: row["_headcall"][key] for key in ("head_calls", "target_template", "head_derived")}}
               if is_headcall(row) and weight else None for row, weight in zip(rows, weights)]
    needed = [index for index, sample in enumerate(samples) if sample is not None and sampler.chosen(sample, step)]
    total = matched_count(len(needed), fsdp, process_group, device)
    changed, out = False, list(encodings)
    for index in needed:
        row, encoding, sample_row = rows[index], encodings[index], samples[index]
        prompt = prompt_batch(encoding, device)
        sampler.heads = sampling.heads_factory(model, prompt, forward_context)
        stats["session_forwards"] += 1
        context = HeadContext(prompt["input_ids"][0].tolist(), key=row.get("qid"), row=sample_row, batch=prompt)
        new, replaced = sampler(sample_row, step, context)
        sampler.heads = None
        if not replaced:
            continue
        spliced = splice(processor, encoding, row, new["target"], max_length=max_length)
        if spliced is None:
            stats["swaps_rejected_length"] += 1
            continue
        out[index], changed = spliced, True
        stats["rows_swapped"] += 1
        stats["responses_swapped"] += len(replaced)
    for _ in range(total - len(needed)):
        discarded_forward(model, prompt_batch(encodings[0], device), forward_context)
        stats["discarded_forwards"] += 1
    if not changed:
        return batch
    collated = collate_rows(out, processor.tokenizer.pad_token_id)
    return {key: value.to(device) for key, value in collated.items()}
