"""One-pass source parsing, bounded scene cache and append-only output shards."""
import gzip
import hashlib
import io
import itertools
import sqlite3
from collections import Counter, OrderedDict, defaultdict, deque
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from .balance import candidates, shortages, targets
from .bindings import gt_label, question
from .common import ProvenanceError, Refusal, digest, encoded, loads, pinned, read_json, sha256, write_json
from .geometry import GTScene, frame_intrinsics, rgb_hashes
from .program import generate
from .provenance import Admission, adapters, l1_api, rung1_alias, validate_build
from .replay import audit
from .review import Lengths, rewrite_gate


def gt_head_targets(scene):
    """Encode all 32 GT cameras for P3's OwnGeometry hybrid head readouts.

    carrier_c1_routing.py:207-223 in p3_build/work/c1mix/student_pilot
    inverts E_k = inv(C_k) C_1; its FoVs are vertical then horizontal, in radians.
    Gravity is world +z expressed in frame 1's native OpenCV camera axes.
    """
    missing = [k for k in range(1, 33) if not scene.gt.has(k)]
    if missing:
        raise Refusal("missing_gt_pose9_frames", detail=encoded(missing))
    R1, t1 = scene.gt.cam(1)
    poses = []
    for k in range(1, 33):
        K = frame_intrinsics(scene.gt, k)
        fov = [2 * np.arctan(scene.gt.H / (2 * K[1, 1])),
               2 * np.arctan(scene.gt.W / (2 * K[0, 0]))]
        Rk, tk = scene.gt.cam(k)
        q = Rotation.from_matrix(Rk.T @ R1).as_quat()
        if q[3] < 0:
            q = -q
        poses.append([*(Rk.T @ (t1 - tk)), *q, *fov])
    # The reference camera is the identity, including with float32 source poses.
    poses[0][:7] = [0., 0., 0., 0., 0., 0., 1.]
    up = R1.T @ np.array([0., 0., 1.])
    return {"gt_pose9": np.asarray(poses, dtype=np.float64).tolist(),
            "gt_up": up.tolist()}


def gt_camera_raw(scene, record):
    """Retain GT camera metres before the trace rounds points to two decimals.

    Keys are depth_at point labels (camera-node ids for legacy traces). Values
    use public axes: x right, y up, z forward, preserving GT adapter precision.
    Correction-initial clicks are included; RGB-only clicks have no depth label.
    """
    import copy
    scene = copy.copy(scene)
    scene.head_layout = record.get("head_layout") or record["private"].get("head_layout") or getattr(scene, "head_layout", "paired_anchor")
    points = {}
    for click in record["private"]["clicks"]:
        label = click.get("label", click.get("camera_node"))
        if label is None:
            continue
        value = scene.readout(click["instance_id"], click["frame"], click["uv"])
        points[label] = [float(x * sign) for x, sign in zip(value["camera"], (1, -1, 1))]
    return points


class HashReader(io.RawIOBase):
    def __init__(self, file):
        self.file, self.h = file, hashlib.sha256()

    def readable(self): return True

    def readinto(self, b):
        n = self.file.readinto(b)
        if n: self.h.update(memoryview(b)[:n])
        return n


def stream(pin, limit=None):
    """Hash compressed bytes during their only read. Limited builds drain remaining
    bytes for provenance, but do not parse or claim coverage of the remaining rows.
    """
    path = Path(pin["path"])
    if not path.is_absolute() or not str(path.resolve()).startswith("/scratch/"):
        raise ProvenanceError("source path must be on scratch")
    with path.open("rb") as raw:
        reader = HashReader(raw)
        buffered = io.BufferedReader(reader)
        payload = gzip.GzipFile(fileobj=buffered) if str(path).endswith(".gz") else buffered
        with io.TextIOWrapper(payload) as text:
            n = 0
            while limit is None or n < limit:
                line = text.readline(2*1024*1024+1)
                if not line: break
                if len(line) > 2*1024*1024: raise ProvenanceError("source row exceeds 2 MiB")
                n += 1
                try: row = loads(line)
                except (ValueError, TypeError): row = {"_malformed_json": True}
                yield n, row
            # Draining the decoder preserves a verifiable compressed-file hash even
            # when it already read ahead into its buffered input.
            for _ in iter(lambda: text.read(1024*1024), ""):
                pass
            if reader.h.hexdigest() != pin["sha256"]:
                raise ProvenanceError("source SHA mismatch: " + str(path))


class Shards:
    def __init__(self, output, prefix, size=1000):
        self.output, self.prefix, self.size = output, prefix, size
        self.count, self.files, self.raw, self.gz = 0, [], None, None

    def write(self, row):
        if self.count % self.size == 0:
            self.close()
            path = self.output / f"{self.prefix}-{len(self.files):05d}.jsonl.gz"
            self.raw = path.open("xb")
            self.gz = gzip.GzipFile(filename="", mode="wb", fileobj=self.raw, mtime=0)
            self.files.append(path)
        self.gz.write((encoded(row)+"\n").encode())
        self.count += 1

    def close(self):
        if self.gz:
            self.gz.close(); self.raw.close()
            self.gz = self.raw = None


class Builder:
    def __init__(self, config, output, infrastructure):
        self.config, self.output, self.infrastructure = config, output, infrastructure
        if str(config.get("trace_form", "")).startswith("canonical") and config["trace_form"] != "canonical_v38":
            raise ProvenanceError("stale canonical configuration; replay v3.7 with its frozen producer")
        self.preview_per_type = config.get("canonical_preview_per_type")
        if self.preview_per_type is not None:
            if (type(self.preview_per_type) is not int or not 1 <= self.preview_per_type <= 2
                    or config.get("trace_form") != "canonical_v38"
                    or config.get("generation_stage", "pilot") != "pilot"
                    or config.get("additions", {}).get("max_candidates") != 0):
                raise ProvenanceError("canonical preview needs a 1..2 per-type quota, pilot mode and disabled balancing additions")
        self.source_schedule = config.get("source_schedule", "source_order")
        if self.source_schedule not in ("source_order", "review_type_coverage"):
            raise ProvenanceError("unknown source schedule")
        if self.source_schedule == "review_type_coverage" and (
                self.preview_per_type is not None or config.get("trace_form") != "canonical_v38"
                or config.get("generation_stage", "pilot") not in ("pilot", "review_pool")
                or config.get("additions", {}).get("max_candidates") != 0):
            raise ProvenanceError("review scheduling requires canonical pilot/review scope, no per-type quota and no additions")
        self.programs, self.T = adapters(config)
        self.l1 = l1_api(config)
        self.lengths = Lengths(config)
        self.admission = Admission(config, infrastructure)
        self.cache = OrderedDict()
        cache_size = config.get("scene_cache_size", 1)
        if type(cache_size) is not int or not 1 <= cache_size <= 5: raise ProvenanceError("scene cache must be 1..5")
        self.cache_size = cache_size
        self.db = sqlite3.connect(output / "INDEX.sqlite")
        self.db.execute("PRAGMA journal_mode=MEMORY")
        self.db.execute("PRAGMA temp_store=MEMORY")
        self.db.execute("PRAGMA cache_size=-4096")
        self.db.execute("CREATE TABLE seen(qid TEXT PRIMARY KEY, question TEXT UNIQUE)")
        self.db.execute("CREATE TABLE plans(qid TEXT PRIMARY KEY, payload TEXT)")
        self.db.execute("CREATE TABLE rewrites(qid TEXT PRIMARY KEY, payload TEXT)")
        self.db.execute("CREATE TABLE input_joins(qid TEXT PRIMARY KEY, payload TEXT)")
        self.stats, self.reasons, self.census = Counter(), Counter(), Counter()
        self.by_type, self.mix = Counter(), defaultdict(Counter)
        self.review, self.used_scenes = defaultdict(list), {}
        size = config.get("shard_rows", 1000)
        if type(size) is not int or not 1 <= size <= 10000: raise ProvenanceError("shard_rows must be 1..10000")
        self.accepted = Shards(output, "accepted", size)
        self.private = Shards(output, "evidence", size)
        self.dispositions = Shards(output, "dispositions", size)

    def scene(self, row):
        alias, entry = self.admission.entry(row)
        key = digest(entry)
        if key not in self.cache:
            self.cache[key] = GTScene(entry, self.programs)
            self.cache[key].l1 = self.l1
            while len(self.cache) > self.cache_size: self.cache.popitem(last=False)
        self.cache.move_to_end(key)
        self.used_scenes[alias] = entry
        return alias, self.cache[key]

    def plan(self, qid):
        r = self.db.execute("SELECT payload FROM plans WHERE qid=?", (qid,)).fetchone()
        return loads(r[0]) if r else None

    def load_plans(self):
        for pin in self.config.get("reviewed_plans", []):
            for _, r in stream(pin):
                if not isinstance(r, dict) or r.get("reviewed") is not True:
                    raise ProvenanceError("only normalized reviewed bindings may be indexed")
                try:
                    self.db.execute("INSERT INTO plans VALUES (?,?)", (r["qid"], encoded(r)))
                except sqlite3.IntegrityError as e: raise ProvenanceError("duplicate reviewed plan qid") from e
        self.db.commit()
        for pin in self.config.get("student_input_joins", []):
            for _, r in stream(pin):
                if not isinstance(r.get("student_input"), dict): raise ProvenanceError("normalized student-input join required")
                try: self.db.execute("INSERT INTO input_joins VALUES (?,?)", (r["qid"], encoded(r)))
                except sqlite3.IntegrityError as e: raise ProvenanceError("duplicate student-input join qid") from e
        self.db.commit()
        for pin in self.config.get("reviewed_rewrites", []):
            for _, r in stream(pin):
                try: self.db.execute("INSERT INTO rewrites VALUES (?,?)", (r["qid"], encoded(r)))
                except sqlite3.IntegrityError as e: raise ProvenanceError("duplicate rewrite qid") from e
        self.db.commit()

    def process(self, row, source, line, addition=False):
        self.stats["seen"] += 1
        kind = row.get("question_type", "UNKNOWN") if isinstance(row, dict) else "UNKNOWN"
        qid = row.get("qid") if isinstance(row, dict) else None
        status = {"source": source, "line": line, "qid": qid, "question_type": kind,
                  "scene": row.get("scene") if isinstance(row, dict) else None,
                  "dataset": row.get("dataset") if isinstance(row, dict) else None,
                  "origin": "gt_addition" if addition else "source"}
        try:
            if not isinstance(row, dict) or row.get("_malformed_json"): raise Refusal("malformed_source_row")
            if not isinstance(qid, str) or not qid: raise Refusal("missing_qid")
            source_row_sha256 = digest(row)
            if bool(row.get("infrastructure_only")) != self.infrastructure: raise Refusal("source_infrastructure_mode")
            if not self.infrastructure and kind in ("room_size_estimation", "object_size_estimation", "absolute_size_object", "relative_size_object"):
                raise Refusal("p3_v1_direct_answer_required", disposition="deferred")
            if not self.infrastructure and self.config.get("generation_stage", "pilot") == "pilot" and self.accepted.count >= 1000:
                raise Refusal("awaiting_first_1000_real_review", disposition="deferred")
            if self.preview_per_type is not None and self.by_type[kind] >= self.preview_per_type:
                raise Refusal("canonical_preview_quota", disposition="deferred")
            join = self.db.execute("SELECT payload FROM input_joins WHERE qid=?", (qid,)).fetchone()
            if join:
                join = loads(join[0])
                if join.get("source_row_sha256") and join["source_row_sha256"] != digest(row):
                    raise ProvenanceError("student-input join source-row mismatch")
                for key in ("scene", "dataset"):
                    if key in join and join[key] != row.get(key): raise ProvenanceError("student-input join identity mismatch")
                si = dict(row.get("student_input") or {})
                for key, value in join["student_input"].items():
                    if key in ("target", "answer", "timestamps", "fps"): continue
                    if key == "frames":
                        # Localize identical bytes; only explicit joins fill an
                        # empty image list. Never replace a conflicting image.
                        if si.get(key) not in (None, []):
                            old, new = rgb_hashes(si[key]), rgb_hashes(value)
                            if old is None or new is None or old != new:
                                raise Refusal("rgb_input_join_mismatch")
                    elif si.get(key) is not None and si[key] != value:
                        raise ProvenanceError("student-input join overwrites source field: " + key)
                    si[key] = value
                row = {**row, "student_input": si}
            alias, scene = self.scene(row)
            scene.check_rgb_input(row.get("student_input") or {}, required=not self.infrastructure)
            status.update(alias=alias, canonical=scene.entry["canonical"], physical_group=scene.entry["physical_group"])
            q = question(row)
            key = digest([scene.entry["physical_group"], q["question_type"], q["question"].strip().lower()])
            try: self.db.execute("INSERT INTO seen VALUES (?,?)", (qid, key))
            except sqlite3.IntegrityError: raise Refusal("duplicate_qid_or_question")
            reviewed = self.plan(qid)
            if self.config.get("trace_form") == "canonical_v38":
                from .canon import generate as canonical
                record = canonical(scene, self.T, self.config, row, reviewed)
            else:
                record = generate(scene, self.T, self.config, row, reviewed)
            if addition: record["private"]["generated_gt"] = row["generated_gt"]
            census = audit(record, scene, self.T, self.config, row, reviewed)
            record.update(gt_head_targets(scene))
            record.setdefault("head_layout", self.config.get("head_layout", "paired_anchor"))
            record["gt_camera_raw"] = gt_camera_raw(scene, record)
            private = record.pop("private")
            private["source_answer"] = row["answer"]
            private["gt_label"] = gt_label(row)
            lineage = {k: row[k] for k in ("benchmark_trained_diagnostic", "provisional_diagnostic", "benchmark_improvement_claim",
                       "score_nomination_allowed", "result_status", "pool", "category", "generation_commit", "validation_commit", "label_source", "license_ref", "agree_released") if k in row}
            private["source_diagnostic_lineage"] = lineage
            rewrite = self.db.execute("SELECT payload FROM rewrites WHERE qid=?", (qid,)).fetchone()
            if rewrite:
                rewrite = loads(rewrite[0])
                selected = rewrite_gate(record["target"], rewrite["target"], rewrite["evidence"])
                if selected != record["target"]:
                    from .trace import loss_spans, remap_tool_spans
                    record["tool_output_spans"] = remap_tool_spans(record["target"], selected, record["tool_output_spans"])
                    record["loss_spans"] = loss_spans(selected, record["tool_output_spans"])
                    record["original_target"], record["target"] = record["target"], selected
                    private["style_evidence"] = rewrite["evidence"]
            record["length"] = self.lengths.observe(kind, record["target"])
            self.census.update(census)
            record.update(infrastructure_only=self.infrastructure, source_qid=qid,
                          provenance={"source": source, "line": line,
                                      "alias": rung1_alias(scene.entry["canonical"], alias), "source_alias": alias,
                                      "canonical": scene.entry["canonical"], "physical_group": scene.entry["physical_group"],
                                      "frame_indices": scene.entry["frame_indices"], "gt_sha256": scene.entry["gt"]["sha256"],
                                      "rgb_manifest": scene.entry["rgb_manifest"],
                                      "rgb_join": scene.entry.get("rgb_binding", "byte_verified"),
                                      "source_row_sha256": source_row_sha256,
                                      "source_question_sha256": private["source_question_sha256"],
                                      "source_diagnostic_lineage": lineage,
                                      "score_nomination_allowed": False, "training_eligibility": "pending_release_gates"})
            self.accepted.write(record)
            self.private.write({"qid": qid, **private})
            self.by_type[kind] += 1
            decision = next(e for e in record["events"] if e["kind"] == "decision")
            self.mix[kind][str(decision["result"])] += 1
            # Keep the five lowest qid hashes per type, independent of stream order.
            sample = self.review[kind]
            sample.append((digest(qid), record))
            sample.sort(key=lambda pair: pair[0]); del sample[5:]
            status.update(disposition="accepted", reason="observable_program_and_independent_replay")
        except Refusal as e:
            status.update(disposition=e.disposition, reason=e.reason, detail=e.detail)
            self.reasons[e.reason] += 1
        except (KeyError, TypeError, IndexError) as e:
            # Missing row inputs defer one row. Asset/provenance errors never enter
            # this handler: those use ProvenanceError and abort the whole build.
            status.update(disposition="deferred", reason="missing_or_malformed_row_input", detail=str(e))
            self.reasons[status["reason"]] += 1
        self.stats[status["disposition"]] += 1
        self.stats["additions_seen" if addition else "source_seen"] += 1
        self.dispositions.write(status)
        if self.stats["seen"] % 100 == 0: self.db.commit()
        return status

    def additions(self, distribution):
        policy = self.config.get("additions", {})
        wanted = targets(distribution, self.mix, policy.get("minimum_per_type"))
        budget = policy.get("max_candidates", 0)
        attempts, candidate_count = 0, 0
        if type(budget) is not int or budget < 0: raise ProvenanceError("invalid addition budget")
        if budget:
            visited = set()
            for alias in sorted(self.admission.scenes):
                if not any(n for c in shortages(wanted, self.mix).values() for n in c.values()): break
                entry = self.admission.scenes[alias]
                key = digest([entry["canonical"], entry["physical_group"], entry["frame_indices"]])
                if key in visited: continue
                visited.add(key)
                stub = {"scene": alias, "student_input": {"frame_indices": entry["frame_indices"]}}
                try: _, scene = self.scene(stub)
                except Refusal: continue
                for row, label in candidates(scene, alias, self.T, self.config):
                    candidate_count += 1
                    t = row["question_type"]
                    if self.mix[t][label] < wanted[t].get(label, 0):
                        self.process(row, "generated_gt", candidate_count, addition=True)
                        attempts += 1
                    if candidate_count >= budget or not any(n for c in shortages(wanted, self.mix).values() for n in c.values()): break
                if candidate_count >= budget: break
        return {"targets": wanted, "shortages": shortages(wanted, self.mix), "candidates_examined": candidate_count,
                "attempts": attempts, "candidate_budget": budget, "source_direction_rows_dropped_for_balance": 0}

    def close(self):
        for writer in (self.accepted, self.private, self.dispositions): writer.close()
        self.db.commit(); self.db.close()


def process_review_sources(builder, inputs):
    """Prioritize types with fewer admitted rows; retain every source and disposition."""
    pending, source_counts = defaultdict(deque), []
    size = count = 0
    for pin in inputs:
        n = 0
        for line, row in stream(pin):
            count += 1
            size += len(encoded(row).encode("utf-8"))
            if count > 15000 or size > 256 * 1024**2:
                raise ProvenanceError("review schedule source buffer exceeds its bound")
            kind = row.get("question_type", row.get("category", "unknown")) if isinstance(row, dict) else "unknown"
            if not isinstance(kind, str): kind = "unknown"
            pending[kind].append((row, pin["path"], line))
            n += 1
        if "expected_rows" in pin and n != pin["expected_rows"]:
            raise ProvenanceError("source row count mismatch: " + pin["path"])
        source_counts.append({**pin, "rows_processed": n, "scope": "complete"})
    # Source order breaks ties and remains fixed within each type. Only admitted
    # counts affect the order; answers and calculation values are never inspected.
    priority = {kind: i for i, kind in enumerate(pending)}
    while pending:
        kind = min(pending, key=lambda k: (builder.by_type[k], priority[k]))
        row, path, line = pending[kind].popleft()
        builder.process(row, path, line)
        if not pending[kind]:
            del pending[kind]
    return source_counts


def build(config_path, output, infrastructure=False, limit=None, parent_record=None):
    config = read_json(config_path)
    validate_build(config, config_path, infrastructure, parent_record)
    code_closure = [{"path": str(p.resolve()), "sha256": sha256(p)}
                    for p in sorted(Path(__file__).parent.glob("*.py"))]
    if limit is not None and limit < 0: raise ProvenanceError("negative limit")
    if config.get("source_schedule") == "review_type_coverage" and limit is not None:
        raise ProvenanceError("review scheduling requires complete source scope")
    output = Path(output).resolve()
    allowed = Path("/scratch/jjyeung/orch_cd/derivgen/out")
    if not output.is_relative_to(allowed) or output == allowed:
        raise ProvenanceError("new output directory must be below derivgen/out")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "STARTED.json", {"infrastructure_only": infrastructure, "config_sha256": sha256(config_path),
                                        "limit": limit, "status": "provisional_until_MANIFEST"})
    builder = None
    try:
        builder = Builder(config, output, infrastructure)
        builder.load_plans()
        if builder.source_schedule == "review_type_coverage":
            source_counts = process_review_sources(builder, config["inputs"])
        else:
            source_counts = []
            remaining = limit
            for pin in config["inputs"]:
                n = 0
                source_limit = remaining if remaining is not None else None
                for line, row in stream(pin, source_limit):
                    builder.process(row, pin["path"], line)
                    n += 1
                source_counts.append({**pin, "rows_processed": n, "scope": "limited" if limit is not None else "complete"})
                if limit is None and "expected_rows" in pin and n != pin["expected_rows"]:
                    raise ProvenanceError("source row count mismatch: " + pin["path"])
                if remaining is not None: remaining -= n
        distribution = read_json(pinned(config["benchmark_distribution"]))
        balancing = builder.additions(distribution)
        if builder.stats["seen"] != sum(builder.stats[x] for x in ("accepted", "rejected", "deferred")):
            raise ProvenanceError("source disposition accounting mismatch")
        builder.close()
        write_json(output / "COUNTS.json", {"counts": dict(builder.stats), "by_type": dict(builder.by_type),
                                           "reasons": dict(builder.reasons), "sources": source_counts})
        write_json(output / "UNIT_CENSUS.json", {"events_by_declared_unit": dict(builder.census),
                                                "accepted_rows": builder.accepted.count, "gates": "independent replay"})
        write_json(output / "BALANCE.json", balancing)
        write_json(output / "TRACE_LENGTHS.json", builder.lengths.report())
        review = [r for t in sorted(builder.review) for _, r in builder.review[t]]
        with (output / "REVIEW.jsonl").open("x") as f:
            for r in review: f.write(encoded(r)+"\n")
        with (output / "SAMPLES_FOR_USER.md").open("x") as f:
            f.write("# Infrastructure fixtures only\n" if infrastructure else "# Real rows for user and parent review\n")
            for r in review:
                f.write(f"\n## {r['question_type']} — {r['qid']}\n\n{r['question']}\n\n")
                f.write("\n".join(r["options"])+"\n\nOriginal GT rendering:\n\n```text\n"+r.get("original_target", r["target"])+"\n```\n")
                if "original_target" in r:
                    f.write("\nReviewed natural-style rewrite:\n\n```text\n"+r["target"]+"\n```\n")
                else:
                    f.write("\nNatural-style rewrite and Qwen likelihood comparison are pending.\n")
            for t in sorted(config.get("required_review_types", [])):
                count = len(builder.review.get(t, []))
                if count < 5: f.write(f"\nBLOCKED: {t} has {count}/5 valid rendered rows.\n")
        with (output / "MIX.md").open("x") as f:
            f.write("# Accepted mix\n\n" + ("Infrastructure fixtures; zero real training rows.\n\n" if infrastructure else "Parent and independent review required before scale.\n\n"))
            f.write("| Type | Content | Rows |\n|---|---|---:|\n")
            for t, counts in sorted(builder.mix.items()):
                for label, n in sorted(counts.items()): f.write(f"| {t} | {label} | {n} |\n")
            f.write("\nNo accepted direction row was dropped for balancing.\n\nRemaining additive shortages:\n\n```json\n"+encoded(balancing["shortages"])+"\n```\n")
        outputs = sorted(p for p in output.iterdir() if p.is_file())
        for pin in code_closure: pinned(pin)
        manifest = {"schema": "derivgen-build-v1", "status": "infrastructure_only" if infrastructure else "awaiting_parent_and_Claude_review",
                    "code_closure": code_closure,
                    "config": {"path": str(Path(config_path).resolve()), "sha256": sha256(config_path)},
                    "parent_record": parent_record, "spec": config["spec"], "dependencies": config["dependencies"],
                    "authority": config["authority"], "scene_map": config["scene_map"], "membership": config["membership"],
                    "scene_registry": config["scene_registry"], "scenes_used": builder.used_scenes,
                    "inputs": source_counts, "reviewed_plans": config.get("reviewed_plans", []),
                    "student_input_joins": config.get("student_input_joins", []), "row_ready": config.get("row_ready"),
                    "reviewed_rewrites": config.get("reviewed_rewrites", []), "l1": config.get("l1"),
                    "benchmark_distribution": config["benchmark_distribution"],
                    "outputs": [{"path": str(p), "sha256": sha256(p)} for p in outputs],
                    "real_accepted": 0 if infrastructure else builder.accepted.count,
                    "review_only": not infrastructure and config.get("generation_stage") == "review_pool",
                    "complete_source_scope": limit is None,
                    "source_floor": {"weak_expected": 401141, "f17_expected_pending": 380649,
                                     "combined_before_overlap": 781790},
                    "scale_approved": bool(not infrastructure and config.get("generation_stage") == "scale"),
                    "scale_approval": config.get("scale_approval"),
                    "source_floor_met_before_overlap": builder.stats["source_seen"] >= 781790}
        write_json(output / "MANIFEST.json", manifest)
        return manifest
    except BaseException as e:
        if builder:
            # Close owned files while preserving every partial shard and index.
            try: builder.close()
            except (sqlite3.Error, ValueError): pass
        write_json(output / "ABORTED.json", {"exception": type(e).__name__, "message": str(e), "partial_outputs_preserved": True})
        raise
